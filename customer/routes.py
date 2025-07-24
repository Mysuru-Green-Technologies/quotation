from flask import Blueprint, render_template, session, redirect, url_for, request, flash, send_file
import pandas as pd
from datetime import datetime
from io import BytesIO
from extensions import mysql
from MySQLdb.cursors import DictCursor

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/customers')
def customer_list():
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)

    try:
        # Get all customers for the current user
        cursor.execute("""
            SELECT c.*, COUNT(f.followup_id) as pending_followups
            FROM customers c
            LEFT JOIN customer_followups f ON c.customer_id = f.customer_id AND f.status = 'pending' AND f.followup_date <= NOW()
            WHERE c.user_id = %s
            GROUP BY c.customer_id
            ORDER BY c.first_name, c.last_name
        """, (session['userid'],))
        customers = cursor.fetchall()

        # Get upcoming followups
        cursor.execute("""
            SELECT f.*, c.first_name, c.last_name
            FROM customer_followups f
            JOIN customers c ON f.customer_id = c.customer_id
            WHERE f.user_id = %s AND f.status = 'pending' AND f.followup_date >= NOW()
            ORDER BY f.followup_date ASC
            LIMIT 5
        """, (session['userid'],))
        upcoming_followups = cursor.fetchall()

        return render_template('customers/list.html', 
                            customers=customers, 
                            upcoming_followups=upcoming_followups)
    finally:
        cursor.close()

@customer_bp.route('/notifications')
def notifications():
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM notifications
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (session['userid'],))
        notifications = cursor.fetchall()

        return render_template('notifications.html', notifications=notifications)
    finally:
        cursor.close()


@customer_bp.route('/notifications/mark_all_read')
def mark_all_read():
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            UPDATE notifications
            SET is_read = TRUE
            WHERE user_id = %s AND is_read = FALSE
        """, (session['userid'],))
        mysql.connection.commit()
    finally:
        cursor.close()

    return redirect(url_for('customer.notifications'))


@customer_bp.route('/notifications/clear_all')
def clear_all_notifications():
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            DELETE FROM notifications
            WHERE user_id = %s
        """, (session['userid'],))
        mysql.connection.commit()
    finally:
        cursor.close()

    return redirect(url_for('customer.notifications'))

@customer_bp.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if 'userid' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Get form data
        form_data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'company_name': request.form.get('company_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'tax_id': request.form.get('tax_id'),
            'website': request.form.get('website'),
            'status': request.form.get('status'),
            'user_id': session['userid']
        }

        cursor = mysql.connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO customers
                (first_name, last_name, company_name, email, phone, address, 
                 city, state, country, postal_code, tax_id, website, status, user_id)
                VALUES (%(first_name)s, %(last_name)s, %(company_name)s, %(email)s, 
                       %(phone)s, %(address)s, %(city)s, %(state)s, %(country)s, 
                       %(postal_code)s, %(tax_id)s, %(website)s, %(status)s, %(user_id)s)
            """, form_data)

            customer_id = cursor.lastrowid

            # Add notification
            cursor.execute("""
                INSERT INTO notifications
                (user_id, title, message, related_entity_type, related_entity_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['userid'], 
                 "New Customer Added", 
                 f"You added {form_data['first_name']} {form_data['last_name']} to your customer list", 
                 "customer", 
                 customer_id))

            mysql.connection.commit()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customer.customer_detail', customer_id=customer_id))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error adding customer: {str(e)}', 'danger')
        finally:
            cursor.close()

    return render_template('customers/add.html')

@customer_bp.route('/customers/<int:customer_id>')
def customer_detail(customer_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)

    try:
        # Get customer details
        cursor.execute("""
            SELECT * FROM customers 
            WHERE customer_id = %s AND user_id = %s
        """, (customer_id, session['userid']))
        customer = cursor.fetchone()

        if not customer:
            flash('Customer not found or access denied', 'danger')
            return redirect(url_for('customer.customer_list'))

        # Get customer notes
        cursor.execute("""
            SELECT n.*, u.name as user_name
            FROM customer_notes n
            JOIN user u ON n.user_id = u.userid
            WHERE n.customer_id = %s
            ORDER BY n.created_at DESC
        """, (customer_id,))
        notes = cursor.fetchall()

        # Get customer followups
        cursor.execute("""
            SELECT f.*
            FROM customer_followups f
            WHERE f.customer_id = %s AND f.user_id = %s
            ORDER BY f.followup_date DESC
        """, (customer_id, session['userid']))
        followups = cursor.fetchall()

        # Pass current datetime to template
        return render_template('customers/detail.html', 
                            customer=customer, 
                            notes=notes, 
                            followups=followups,
                            now=datetime.now())
    finally:
        cursor.close()

@customer_bp.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)

    try:
        # Get customer details
        cursor.execute("""
            SELECT * FROM customers 
            WHERE customer_id = %s AND user_id = %s
        """, (customer_id, session['userid']))
        customer = cursor.fetchone()

        if not customer:
            flash('Customer not found or access denied', 'danger')
            return redirect(url_for('customer.customer_list'))

        if request.method == 'POST':
            # Get form data
            form_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'company_name': request.form.get('company_name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'country': request.form.get('country'),
                'postal_code': request.form.get('postal_code'),
                'tax_id': request.form.get('tax_id'),
                'website': request.form.get('website'),
                'status': request.form.get('status'),
                'customer_id': customer_id,
                'user_id': session['userid']
            }

            try:
                cursor.execute("""
                    UPDATE customers
                    SET first_name = %(first_name)s, 
                        last_name = %(last_name)s, 
                        company_name = %(company_name)s, 
                        email = %(email)s, 
                        phone = %(phone)s,
                        address = %(address)s, 
                        city = %(city)s, 
                        state = %(state)s, 
                        country = %(country)s, 
                        postal_code = %(postal_code)s,
                        tax_id = %(tax_id)s, 
                        website = %(website)s, 
                        status = %(status)s
                    WHERE customer_id = %(customer_id)s AND user_id = %(user_id)s
                """, form_data)

                mysql.connection.commit()
                flash('Customer updated successfully!', 'success')
                return redirect(url_for('customer.customer_detail', customer_id=customer_id))

            except Exception as e:
                mysql.connection.rollback()
                flash(f'Error updating customer: {str(e)}', 'danger')

        return render_template('customers/edit.html', customer=customer)
    finally:
        cursor.close()

@customer_bp.route('/customers/<int:customer_id>/add-note', methods=['POST'])
def add_customer_note(customer_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    note_text = request.form.get('note_text')

    if not note_text:
        flash('Note text cannot be empty', 'danger')
        return redirect(url_for('customer.customer_detail', customer_id=customer_id))

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO customer_notes
            (customer_id, user_id, note_text)
            VALUES (%s, %s, %s)
        """, (customer_id, session['userid'], note_text))

        mysql.connection.commit()
        flash('Note added successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error adding note: {str(e)}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('customer.customer_detail', customer_id=customer_id))

@customer_bp.route('/customers/<int:customer_id>/add-followup', methods=['POST'])
def add_customer_followup(customer_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    followup_date = request.form.get('followup_date')
    followup_type = request.form.get('followup_type')
    followup_notes = request.form.get('followup_notes')

    if not followup_date or not followup_type:
        flash('Followup date and type are required', 'danger')
        return redirect(url_for('customer.customer_detail', customer_id=customer_id))

    cursor = mysql.connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO customer_followups
            (customer_id, user_id, followup_date, followup_type, followup_notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (customer_id, session['userid'], followup_date, followup_type, followup_notes))

        # Add notification
        cursor.execute("""
            INSERT INTO notifications
            (user_id, title, message, related_entity_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['userid'], 
             "New Followup Added", 
             f"You scheduled a {followup_type} followup", 
             "followup", 
             cursor.lastrowid))

        mysql.connection.commit()
        flash('Followup added successfully!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error adding followup: {str(e)}', 'danger')
    finally:
        cursor.close()

    return redirect(url_for('customer.customer_detail', customer_id=customer_id))

@customer_bp.route('/followups/<int:followup_id>/complete', methods=['POST'])
def complete_followup(followup_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)

    try:
        # Verify the followup belongs to the user
        cursor.execute("""
            SELECT * FROM customer_followups 
            WHERE followup_id = %s AND user_id = %s
        """, (followup_id, session['userid']))
        followup = cursor.fetchone()

        if not followup:
            flash('Followup not found or access denied', 'danger')
            return redirect(url_for('customer.customer_list'))

        # Update followup status
        cursor.execute("""
            UPDATE customer_followups
            SET status = 'completed', updated_at = CURRENT_TIMESTAMP
            WHERE followup_id = %s
        """, (followup_id,))

        # Get customer details for notification
        cursor.execute("""
            SELECT first_name, last_name FROM customers 
            WHERE customer_id = %s
        """, (followup['customer_id'],))
        customer = cursor.fetchone()

        # Add notification
        cursor.execute("""
            INSERT INTO notifications
            (user_id, title, message, related_entity_type, related_entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (session['userid'], 
             "Followup Completed",
             f"You completed a {followup['followup_type']} followup with {customer['first_name']} {customer['last_name']}",
             "followup", 
             followup_id))

        mysql.connection.commit()
        flash('Followup marked as completed!', 'success')
    except Exception as e:
        mysql.connection.rollback()
        flash(f'Error completing followup: {str(e)}', 'danger')
    finally:
        cursor.close()

    return redirect(request.referrer or url_for('customer.customer_list'))

@customer_bp.route('/customers/export')
def export_customers():
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)

    try:
        # Get all customers for the current user
        cursor.execute("""
            SELECT 
                first_name, last_name, company_name, email, phone, address, 
                city, state, country, postal_code, tax_id, website, status, 
                DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i:%%s') as created_at
            FROM customers
            WHERE user_id = %s
        """, (session['userid'],))
        customers = cursor.fetchall()

        if not customers:
            flash('No customers to export.', 'warning')
            return redirect(url_for('customer.customer_list'))

        # Create DataFrame
        df = pd.DataFrame(customers)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Customers', index=False)
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='customers_export.xlsx'
        )

    except Exception as e:
        flash(f'Error exporting customers: {str(e)}', 'danger')
        return redirect(url_for('customer.customer_list'))
    finally:
        cursor.close()


@customer_bp.route('/followup/<int:followup_id>', endpoint='detail')
def detail(followup_id):
    if 'userid' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(DictCursor)
    try:
        cursor.execute("""
            SELECT 
                cf.*, 
                CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
                c.company_name,
                c.email,
                c.phone
            FROM customer_followups cf
            JOIN customers c ON c.customer_id = cf.customer_id
            WHERE cf.followup_id = %s
        """, (followup_id,))
        followup = cursor.fetchone()

        if not followup:
            return "Follow-up not found", 404

        return render_template('followup_detail.html', followup=followup)
    finally:
        cursor.close()
     