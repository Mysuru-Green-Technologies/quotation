from flask import Flask,flash, render_template, request, redirect, url_for, session,jsonify, send_file,send_from_directory
from flask_mysqldb import MySQL
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import random
from fpdf import FPDF
from flask import Flask, render_template, redirect, url_for, request
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import black,green
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
import os
from datetime import datetime,timedelta
from reportlab.lib.enums import TA_CENTER
from werkzeug.utils import secure_filename
from flask import request, redirect, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from pypdf import PdfWriter, PdfReader
import tempfile
from datetime import datetime, timedelta
from num2words import num2words  
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from babel.numbers import format_currency
import uuid
from flask import request, session, redirect, url_for, render_template
from customer.routes import customer_bp


app = Flask(__name__, template_folder=r'templates')
app.register_blueprint(customer_bp)

@app.template_filter('datetime_format')
def datetime_format(value, format='%Y-%m-%d'):
    if value is None:
        return ''
    return value.strftime(format)
app.config["TEMPLATES_AUTO_RELOAD"] = True 
app.config["TEMPLATES_AUTO_RELOAD"] = True  

app.secret_key = 'MRET' 

# MySQL Configuration
app.config['MYSQL_HOST'] = '192.168.0.174'
app.config['MYSQL_USER'] = 'remote_control'
app.config['MYSQL_PASSWORD'] = 'Remote_control'
app.config['MYSQL_DB'] = 'quotation_data'

mysql = MySQL(app)

# Configure file uploads
UPLOAD_FOLDER = 'static/uploads'  # Directory where uploaded files will be saved
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed file extensions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def create_tables():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            userid INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            lastname VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            phone_number VARCHAR(15),
            password VARCHAR(100) NOT NULL
        )
    ''')


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            device_id INT AUTO_INCREMENT PRIMARY KEY,
            project_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            project_id VARCHAR(50) NOT NULL,
            FOREIGN KEY (email) REFERENCES user(email) ON DELETE CASCADE
        )
    ''')

    mysql.connection.commit()
    cursor.close()

# Ensure tables are created when the application starts
with app.app_context():
    create_tables()
    
@app.context_processor
def inject_request():
    return dict(request=request)


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT userid, name, lastname, email, phone_number, password, role FROM user WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[5], password):
            session['userid'] = user[0]
            session['name'] = user[1]
            session['email'] = user[3]
            session['role'] = user[6]

            if user[6] == 'admin':
                session['admin'] = True
                flash('Admin login successful!', 'success')
                return redirect(url_for('create_user'))
            elif user[6] == 'employee':
                session['employee'] = True
                flash('Employee login successful!', 'success')
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('login.html')

@app.route('/admin/create_user', methods=['GET', 'POST'])
def create_user():
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        first = request.form['first']
        last = request.form['last']
        email = request.form['email']
        phone_number = request.form['phone']
        role = request.form['role']
        password = request.form['password']
        department=request.form['department']
        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO user (name, lastname, email,phone_number, role, password,department) VALUES (%s, %s, %s, %s, %s, %s,%s)",
            (first, last, email,phone_number, role, hashed_password,department))

            mysql.connection.commit()
            flash('User created successfully', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error: {str(e)}', 'danger')
        finally:
            cur.close()

    return render_template('create_user.html')



@app.route('/dashboard/logout')
def user_logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('name', None)
    session.pop('email', None)
    return render_template('user_logout.html')



@app.route('/dashboard/dashboardd', methods=['GET', 'POST'])
def dashboardd():
    return render_template('dashboardd.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        password = request.form.get('password')
        role=request.form.get('role')

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not name or not password or not email:
            message = 'Please fill out the form!'
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO user (name, lastname, email, phone_number, password,role) VALUES (%s, %s, %s, %s, %s,%s)',
                (name, lastname, email, phone_number, hashed_password,role))
            mysql.connection.commit()
            cursor.close()
            message = 'You have successfully registered!'
            return render_template('login.html', message=message)
    
    # Render the same registration page for GET requests
    return render_template('index.html', message=message if 'message' in locals() else None)
    
@app.route('/dashboard')
def dashboard():
    if not session.get('loggedin') or session.get('role') != 'employee':
        flash("Please log in as employee", "danger")
        user_id = session['userid']
        cursor = mysql.connection.cursor()

        # Dates
        today = datetime.today()
        start_of_this_month = today.replace(day=1)
        start_of_last_month = (start_of_this_month - timedelta(days=1)).replace(day=1)
        end_of_last_month = start_of_this_month - timedelta(days=1)

        # --- TOTAL QUOTATIONS ---
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_this_month.date(), today.date()))
        total_this_month = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_last_month.date(), end_of_last_month.date()))
        total_last_month = cursor.fetchone()[0]

        if total_last_month == 0:
            total_change = 100 if total_this_month > 0 else 0
            total_direction = 'up' if total_this_month > 0 else 'same'
        else:
            total_change = round((total_this_month - total_last_month) / total_last_month * 100)
            total_direction = 'up' if total_this_month > total_last_month else 'down'

        # --- ACCEPTED ---
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Accepted' AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_this_month.date(), today.date()))
        accepted_this_month = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Accepted' AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_last_month.date(), end_of_last_month.date()))
        accepted_last_month = cursor.fetchone()[0]

        if accepted_last_month == 0:
            accepted_change = 100 if accepted_this_month > 0 else 0
            accepted_direction = 'up' if accepted_this_month > 0 else 'same'
        else:
            accepted_change = round((accepted_this_month - accepted_last_month) / accepted_last_month * 100)
            accepted_direction = 'up' if accepted_this_month > accepted_last_month else 'down'

        # --- SENT ---
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Sent' AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_this_month.date(), today.date()))
        sent_this_month = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Sent' AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_last_month.date(), end_of_last_month.date()))
        sent_last_month = cursor.fetchone()[0]

        if sent_last_month == 0:
            sent_change = 100 if sent_this_month > 0 else 0
            sent_direction = 'up' if sent_this_month > 0 else 'same'
        else:
            sent_change = round((sent_this_month - sent_last_month) / sent_last_month * 100)
            sent_direction = 'up' if sent_this_month > sent_last_month else 'down'

        # --- DECLINED ---
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Declined' AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_this_month.date(), today.date()))
        declined_this_month = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Declined' AND created_at BETWEEN %s AND %s", 
                       (user_id, start_of_last_month.date(), end_of_last_month.date()))
        declined_last_month = cursor.fetchone()[0]

        if declined_last_month == 0:
            declined_change = 100 if declined_this_month > 0 else 0
            declined_direction = 'up' if declined_this_month > 0 else 'same'
        else:
            declined_change = round((declined_this_month - declined_last_month) / declined_last_month * 100)
            declined_direction = 'up' if declined_this_month > declined_last_month else 'down'
        # total_change = min(100, round((total_this_month - total_last_month) / total_last_month * 100))


        # --- RECENT 5 QUOTATIONS ---
        cursor.execute("""
            SELECT quotation_number, customer_name, quotation_date, total_amount, status 
            FROM quotations 
            WHERE user_id = %s            
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        recent_quotations = cursor.fetchall()

        # --- Total Counts (for Display) ---
        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Accepted'", (user_id,))
        accepted = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Sent'", (user_id,))
        sent = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Declined'", (user_id,))
        declined = cursor.fetchone()[0]

        cursor.close()

        return render_template(
            'dashboardd.html',
            name=session['name'],
            total_quotations=total_this_month,
            total_change=total_change,
            total_direction=total_direction,
            accepted=accepted,
            accepted_change=accepted_change,
            accepted_direction=accepted_direction,
            sent=sent,
            sent_change=sent_change,
            sent_direction=sent_direction,
            declined=declined,
            declined_change=declined_change,
            declined_direction=declined_direction,
            recent_quotations=recent_quotations
        )
    else:
        return redirect(url_for('login'))

    
@app.route('/api/total_quotations')
def api_total_quotations():
    if 'userid' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['userid']
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT id FROM quotations where user_id=%s
            UNION ALL
            SELECT id FROM Existing_quotations where user_id=%s
        ) AS combined
    """,(user_id, user_id))
    total = cursor.fetchone()[0]
    cursor.close()
    return {'total_quotations': total}

@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if 'userid' not in session:
        return redirect(url_for('login'))

    if 'avatar' not in request.files:
        flash('No file selected')
        return redirect(url_for('user_profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('user_profile'))

    if file and allowed_file(file.filename):
        # Secure the filename and ensure unique name
        filename = secure_filename(f"{session['userid']}.{file.filename.rsplit('.', 1)[1].lower()}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(filepath)
        
        # Update database with filename
        cursor = mysql.connection.cursor()
        cursor.execute('UPDATE user SET avatar = %s WHERE userid = %s', 
                      (filename, session['userid']))
        mysql.connection.commit()
        cursor.close()
        
        # Update session if needed
        session['avatar'] = filename
        
        flash('Profile picture updated successfully!')
    else:
        flash('Allowed file types are: png, jpg, jpeg, gif')

    return redirect(url_for('user_profile'))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/dashboard/user_profile')
def user_profile():
    if 'userid' not in session:
        return redirect(url_for('login'))

    userid = session['userid']
    cursor = mysql.connection.cursor()

    try:
        # Get user profile info
        cursor.execute("SELECT name, lastname, email, phone_number,last_updated,department FROM user WHERE userid = %s", (userid,))
        user = cursor.fetchone()

        if not user:
            flash("User not found.")
            return redirect(url_for('login'))

        name, lastname, email, phone_number, last_updated,department  = user

        # Total quotations from both tables
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT id FROM quotations WHERE user_id = %s
                UNION ALL
                SELECT id FROM Existing_quotations WHERE user_id = %s
            ) AS combined
        """, (userid, userid))
        total_quotations = cursor.fetchone()[0]

        # Accepted quotations count
        cursor.execute("""
            SELECT COUNT(*) FROM quotations WHERE user_id = %s AND status = 'Accepted'
        """, (userid,))
        accepted = cursor.fetchone()[0]
        cursor.execute("""
    SELECT quotation_number , created_at
    FROM quotations 
    WHERE user_id = %s AND status = 'Accepted' 
    ORDER BY created_at DESC 
    LIMIT 1
""", (userid,))
        recent_accept = cursor.fetchone()
        recent_accept_number = recent_accept[0] if recent_accept else '-'
        recent_accept_time = recent_accept[1] if recent_accept else None
        
        # Most recent quotation number
        cursor.execute("""
            SELECT quotation_number , created_at
            FROM quotations 
            WHERE user_id = %s
            ORDER BY created_at DESC 
            LIMIT 1
        """, (userid,))
        recent = cursor.fetchone()
        recent_quotation_number = recent[0] if recent else '—'
        recent_created_time = recent[1] if recent else None

        return render_template(
            'user_profile.html',
            name=name,
            lastname=lastname,
            department=department,
            email=email,
            phone_number=phone_number,
            total_quotations=total_quotations,
            accepted=accepted,
            recent_quotation_number=recent_quotation_number,
            recent_created_time=recent_created_time,
            recent_accept=recent_accept_number,
            recent_accept_time=recent_accept_time,
            last_updated=last_updated,
        )

    finally:
        cursor.close()

@app.route('/update_user_details', methods=['POST'])
def update_user_details():
    if 'userid' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    userid = session['userid']
    name = request.form.get('name', '')
    lastname = request.form.get('lastname', '')
    new_email = request.form.get('email', '')
    phone_number = request.form.get('phone', '')

    cursor = mysql.connection.cursor()

    try:
        # Fetch the user details to ensure the user exists
        cursor.execute('SELECT * FROM user WHERE userid = %s', (userid,))
        account = cursor.fetchone()

        if account:
            old_email = account[3]  # Assuming email is the 4th field in the user table

            # Update email if changed and ensure email is valid and not taken
            if new_email != old_email:
                cursor.execute('SELECT * FROM user WHERE email = %s', (new_email,))
                email_account = cursor.fetchone()
                if email_account:
                    message = 'The new email address is already registered!'
                    flash(message)
                    return redirect(url_for('user_profile'))
                
                cursor.execute('UPDATE devices SET email = %s WHERE email = %s', (new_email, old_email))
                session['email'] = new_email  # Update session with the new email

            # Update the user details
            cursor.execute('UPDATE user SET email = %s, name = %s, lastname = %s, phone_number = %s WHERE userid = %s', 
                           (new_email, name, lastname, phone_number, userid))
            message = 'Profile updated successfully!'
            mysql.connection.commit()
        else:
            message = 'User does not exist!'
    except Exception as e:
        mysql.connection.rollback()
        message = f'Error: {str(e)}'
    finally:
        cursor.close()

    flash(message)
    return redirect(url_for('user_profile'))
@app.route('/Quotation')
def quotation():
    return render_template('Quotation.html')
@app.route('/Existing')
def existing():
    return render_template('existing.html')
@app.route('/quotation_tracker')
def quotation_tracker():
    return render_template('quotation_tracker.html')
@app.route('/api/quotations', methods=['GET'])
def get_quotations():
    if 'userid' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    userid = session['userid']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT q.*, 
               (SELECT COUNT(*) FROM quotations WHERE revision_of = q.id) as revision_count
        FROM quotations q WHERE q.user_id = %s
        ORDER BY created_at DESC
    """, (userid,))
    columns = [col[0] for col in cur.description]
    quotations = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    return jsonify(quotations)

@app.route('/api/quotations/<int:quotation_id>', methods=['GET'])
def get_quotation(quotation_id):
    if 'userid' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = session['userid']
    cur = mysql.connection.cursor()

    try:
        # --- Get quotation details ---
        cur.execute("SELECT * FROM userre.quotations WHERE id = %s AND user_id = %s", (quotation_id, user_id))
        quotation = cur.fetchone()
        if not quotation:
            return jsonify({'error': 'Quotation not found'}), 404
        quotation_columns = [col[0] for col in cur.description]
        quotation_dict = dict(zip(quotation_columns, quotation))

        # --- Get items (remove user_id if not present in table) ---
        cur.execute("SELECT * FROM userre.quotation_items WHERE quotation_id = %s", (quotation_id,))
        items = cur.fetchall()
        item_columns = [col[0] for col in cur.description]
        items_list = [dict(zip(item_columns, item)) for item in items]

        # --- Get tracking history ---
        try:
            cur.execute("SELECT * FROM userre.quotation_tracking WHERE quotation_id = %s AND user_id = %s ORDER BY event_date DESC", (quotation_id, user_id))
            history = cur.fetchall()
            history_columns = [col[0] for col in cur.description]
            history_list = [dict(zip(history_columns, h)) for h in history]
        except Exception as e:
            print(f"Error fetching tracking history: {str(e)}")
            history_list = []

        # --- Get reminders (remove user_id if not present in table) ---
        try:
            cur.execute("""
            SELECT * FROM userre.quotation_reminders 
            WHERE quotation_id = %s
            ORDER BY reminder_date
            """, (quotation_id,))
            reminders = cur.fetchall()
            reminders_columns = [col[0] for col in cur.description]
            reminders_list = [dict(zip(reminders_columns, r)) for r in reminders]
        except Exception as e:
            print(f"Error fetching reminders: {str(e)}")
        reminders_list = []

        return jsonify({
            'quotation': quotation_dict,
            'items': items_list,
            'history': history_list,
            'reminders': reminders_list
        })

    except Exception as e:
        import traceback
        print("Error in get_quotation():", str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()



@app.route('/api/quotations/<int:quotation_id>/status', methods=['PUT'])
def update_quotation_status(quotation_id):
    data = request.get_json()
    new_status = data.get('status')
    notes = data.get('notes', '')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    cur = mysql.connection.cursor()
    
    try:
        # Get current status
        cur.execute("SELECT status FROM quotations WHERE id = %s", (quotation_id,))
        current_status = cur.fetchone()[0]
        
        # Update status
        cur.execute("""
            UPDATE quotations 
            SET status = %s, notes = %s, last_updated = NOW() 
            WHERE id = %s
        """, (new_status, notes, quotation_id))
        
        # Add to tracking history
        cur.execute("""
            INSERT INTO quotation_tracking 
            (quotation_id, event_type, details,user_id)
            VALUES (%s, 'Status Changed', %s,%s)
        """, (quotation_id, f"Status changed from {current_status} to {new_status}. Notes: {notes}",session['userid']))
        
        mysql.connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()

@app.route('/api/quotations/<int:quotation_id>/reminders', methods=['POST'])
def add_reminder(quotation_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    required_fields = ['reminder_date', 'reminder_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Prevent past date
    try:
        reminder_date = datetime.strptime(data['reminder_date'], "%Y-%m-%d").date()
        if reminder_date < datetime.now().date():
            return jsonify({'error': 'Reminder date cannot be in the past'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    cur = mysql.connection.cursor()
    
    try:
        # Check if quotation exists
        cur.execute("SELECT id FROM userre.quotations WHERE id = %s", (quotation_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Quotation not found'}), 404

        # Get user ID from session
        user_id = session.get('userid')
        if not user_id:
            return jsonify({'error': 'User not logged in'}), 401

        # Insert reminder with user_id
        cur.execute("""
            INSERT INTO userre.quotation_reminders 
            (quotation_id, reminder_date, reminder_type, notes, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            quotation_id,
            reminder_date,
            data['reminder_type'],
            data.get('notes', ''),
            user_id
        ))

        # Insert tracking event
        cur.execute("""
            INSERT INTO userre.quotation_tracking 
            (quotation_id, event_type, details)
            VALUES (%s, 'Followed Up', %s)
        """, (
            quotation_id,
            f"Reminder set for {data['reminder_date']}. Type: {data['reminder_type']}"
        ))
       
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Reminder created successfully'})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
# Background task for reminders (run daily via cron)
@app.route('/api/reminders/check', methods=['GET'])
def check_reminders():
    cur = mysql.connection.cursor()
    today = datetime.now().date()
    
    user_id = session.get('userid')
    if not user_id:
        return jsonify({'error': 'User not logged in'}), 401

    cur.execute("""
        SELECT r.*, q.quotation_number, q.customer_name, q.quotation_date
        FROM userre.quotation_reminders r
        JOIN userre.quotations q ON r.quotation_id = q.id
        WHERE r.reminder_date >= %s AND r.status = 'Pending' AND r.user_id = %s
    """, (today, user_id))

    reminders = cur.fetchall()
    reminder_list = []

    for reminder in reminders:
        reminder_list.append({
            'quotation_number': reminder[7],
            'customer_name': reminder[8],
            'reminder_date': reminder[2].strftime('%Y-%m-%d'),
            'reminder_type': reminder[3],
            'notes': reminder[5]
        })

    cur.close()
    return jsonify({'reminders': reminder_list})


@app.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    data = request.get_json()
    salutation = data['salutation']
    customer_name = data['customer_name']
    customer_village = data['customer_village']
    customer_email = data['customer_email']
    customer_phone = data['customer_phone']
    subject=data['subject']
    greeting = data['greeting']+","
    total_amount = data['total_amount']
    items = data['items']
    user_id = session.get('userid')  
    discount_type = data.get('discount_type')
    discount_value = float(data.get('discount_value', 0))
    total_amount = sum(float(item.get('total')or 0) for item in data['items'])
        
    

    if not user_id:
        print("user id not found"),400
 
    # Combine salutation and name
    full_name = f"{salutation}.{customer_name}".strip()
    cur = mysql.connection.cursor()
     # For storing in MySQL (this is the correct format MySQL expects)
    mysql_date = datetime.now().strftime("%Y-%m-%d")

    # For displaying to the user
    display_date = datetime.now().strftime("%d-%b-%Y").lower()
 
 
    cur.execute("""
    INSERT INTO quotations (customer_name, customer_village, customer_email, customer_phone, total_amount, created_at, quotation_date, user_id)
    VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
""", (customer_name, customer_village, customer_email, customer_phone, total_amount, mysql_date, user_id))

 
    quotation_id = cur.lastrowid
    quotation_number = f"MGT-{quotation_id:05d}"
 
    cur.execute("""
        UPDATE quotations SET quotation_number = %s WHERE id = %s
    """, (quotation_number, quotation_id))
    mysql.connection.commit()
 
    for item in items:
        try:
            cur.execute("""
                INSERT INTO quotation_items (quotation_id, serial_no, description, quantity, price, gst_percentage, gst_amount, total)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                quotation_id,
                item.get('serial_no', 0) or 0,
                item.get('description', ''),
                item.get('quantity', 0),
                item.get('price', 0.0),
                item.get('gst_percentage', 0.0),
                item.get('gst_amount', 0.0),
                item.get('total', 0.0)
            ))
        except Exception as e:
            print(f"Error inserting item: {e}")
            continue
 
    mysql.connection.commit()
    cur.close()

    original_total = total_amount
    if discount_type == 'percentage':
        discount_amount = (total_amount * discount_value) / 100
    elif discount_type == 'rupees':
        discount_amount = discount_value
    else:
        discount_amount = 0

    grand_total = total_amount - discount_amount
    if grand_total < 0:
        grand_total = 0
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
 
    static_folder = os.path.join(os.getcwd(), r'static\images')
    header_path = os.path.join(static_folder, 'header.png')
    footer_path = os.path.join(static_folder, 'footer.png')
    styles = getSampleStyleSheet()
 
    def draw_header_footer_first_page(canvas, doc):
        width, height = letter
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(270, height - 110, "QUOTATION")
 
    def draw_header_footer_later_pages(canvas, doc):
        width, height = letter
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")
 
    # Combined table: Left side = "To" and details, Right side = quotation number and date
    combined_info_data = [
    [
        Paragraph("<b>To:</b>", styles['Normal']),
        Paragraph(f"<b>Quotation Number:</b> {quotation_number}", ParagraphStyle(name='RightAlign1', parent=styles['Normal'], alignment=TA_RIGHT))
    ],
    [
        Paragraph(full_name, styles['Normal']),
        Paragraph(f"<b>Date:</b> {display_date}", ParagraphStyle(name='RightAlign2', parent=styles['Normal'], alignment=TA_RIGHT))
    ],
    [Paragraph(customer_village, styles['Normal']), ''],
    [Paragraph(customer_email, styles['Normal']), ''],
    [Paragraph(customer_phone, styles['Normal']), ''],
]

    combined_info_table = Table(combined_info_data, colWidths=[300, 240])
    combined_info_table.setStyle(TableStyle([
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 11),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ('BOX', (0, 0), (-1, -1), 0, colors.white),
    ('INNERGRID', (0, 0), (-1, -1), 0, colors.white),
]))

    elements.append(Spacer(1, 50))
    elements.append(combined_info_table)
    elements.append(Spacer(1,5))

    
    # Define centered paragraph style
    centered_subject_style = ParagraphStyle(
    name='CenteredSubject',
    parent=styles['Normal'],
    alignment=TA_LEFT,
    leftIndent=45,          # Push it slightly inward from the left
    spaceBefore=1,
    spaceAfter=1
)
    customer_info = [
    [Paragraph(f"<b>Sub:</b> {subject}", centered_subject_style)],
    [f"{greeting}"]
]

    customer_table = Table(customer_info, colWidths=[460])
    customer_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 0), (-1, -1), 12),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]))

    elements.append(customer_table)
    elements.append(Spacer(1, 20))

 
    # Table Header
    table_data = [["S. No.", "Description", "Qty", "Price", "GST (%)", "GST Amt", "Total"]]
    row_styles = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    def format_inr(value):
            try:
               return format_currency(value, 'INR', locale='en_IN').replace('₹', '').strip()
            except:
               return str(value)
    centered_style = ParagraphStyle(name="Centered", alignment=TA_CENTER)
 
    for i, item in enumerate(items):
        serial_no = str(item.get('serial_no', ''))
        desc_raw = item.get('description', '')
        if "(As per actuals)" in desc_raw:
            clean_desc = Paragraph(desc_raw.replace("(As per actuals)", "").strip(), styles['Normal'] ,)
            table_data.append([serial_no, clean_desc, Paragraph("As per actuals",centered_style), '', '', 'a', ''])
            row_styles.add('SPAN', (2, i + 1), (6, i + 1))
        else:
            description = Paragraph(desc_raw, styles['Normal'])
            quantity = str(item.get('quantity', ''))
            price = format_inr(float(item.get('price') or 0.0))
            gst_percentage = str(item.get('gst_percentage', ''))
            gst_amount = format_inr(float(item.get('gst_amount', 0.0)))
            total = format_inr(float(item.get('total', 0.0)))
 
            table_data.append([
                serial_no, description, quantity, price, gst_percentage, gst_amount, total
            ])
 
    item_table = Table(table_data, colWidths=[40, 180, 60, 60, 60, 70, 80])
    item_table.setStyle(row_styles)
    elements.append(item_table)
    elements.append(Spacer(1, 20))
        # Format total in words
    total_in_words = num2words(grand_total, to='currency', lang='en_IN', currency='INR')
    total_in_words = total_in_words.replace("paise", "Paise").replace("rupees", "Rupees").title()

    # Add "Only" at the end
    if not total_in_words.endswith(" Only"):
        total_in_words += " Only"

        discount_note = ""
        if discount_type == 'percentage':
           discount_note = f"Discount Applied: {discount_value:.2f}%"
        elif discount_type == 'rupees':
           discount_note = f"Discount Applied in Rupees: {discount_value:.2f}"

    # Format numeric value with rupee symbol
    total_formatted = format_currency(total_amount, 'INR', locale='en_IN').replace('₹', '').strip()

    # Create styles
    centered_style = ParagraphStyle(
        name='Centered',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontSize=11,
        leading=14
    )

    left_style = ParagraphStyle(
        name='Left',
        parent=styles['Normal'],
        alignment=TA_LEFT,
        fontSize=11,
        leading=14
    )
    right_style = ParagraphStyle(  # <-- ✅ Add this
    name='Right',
    parent=styles['Normal'],
    alignment=TA_RIGHT,
    fontSize=11,
    leading=14
    )


    grand_total_data = []

# If a discount is applied, show original total and discount
    if discount_amount > 0:
       grand_total_data.append(
        [Paragraph("<b> Total:</b>", left_style), Paragraph(f"{original_total:.2f}", right_style)]
    )
       grand_total_data.append(
        [Paragraph(f"<b>{discount_note}</b>", left_style), Paragraph(f"- {discount_amount:.2f}", right_style)]
    )

# Always show grand total with amount in words
    grand_total_data.append(
    [Paragraph("<b>Grand Total:</b><br/>{}".format(total_in_words), left_style),
     Paragraph(f"<b>{grand_total:.2f}</b>", right_style)]
)

    grand_total_table = Table(grand_total_data, colWidths=[400, 150])




    grand_total_table.setStyle(TableStyle([
        ('FONTNAME', (5, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (1, -1), 'CENTER'),  # Right align the amount
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
 
    elements.append(grand_total_table)
    pdf.build(elements, onFirstPage=draw_header_footer_first_page, onLaterPages=draw_header_footer_later_pages)
 
    buffer.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(buffer.read())
        generated_pdf_path = temp_pdf.name

    # Merge with company.pdf using PdfWriter
    final_writer = PdfWriter()
    company_path = os.path.join(static_folder, "company.pdf")

    with open(company_path, "rb") as company_file:
        company_reader = PdfReader(company_file)
        for page in company_reader.pages:
            final_writer.add_page(page)

    with open(generated_pdf_path, "rb") as quote_file:
        quote_reader = PdfReader(quote_file)
        for page in quote_reader.pages:
            final_writer.add_page(page)

    final_pdf = BytesIO()
    final_writer.write(final_pdf)
    final_pdf.seek(0)
    
    # Clean up the temporary file
    os.unlink(generated_pdf_path)
    
    return send_file(final_pdf, as_attachment=True, download_name="quotation.pdf", mimetype='application/pdf')

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'userid' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not logged in

    userid = session['userid']
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    cursor = mysql.connection.cursor()

    try:
        # Fetch the user details to ensure the user exists
        cursor.execute('SELECT * FROM user WHERE userid = %s', (userid,))
        account = cursor.fetchone()

        if account:
            # Verify current password
            if not check_password_hash(account[5], current_password):  # Assuming password is the 6th field
                message = 'Current password is incorrect!'
            elif new_password != confirm_password:
                message = 'New password and confirm password do not match!'
            else:
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE user SET password = %s WHERE userid = %s', (hashed_password, userid))
                mysql.connection.commit()
                message = 'Password updated successfully!'
        else:
            message = 'User does not exist!'
    except Exception as e:
        mysql.connection.rollback()
        message = f'Error: {str(e)}'
    finally:
        cursor.close()

    flash(message)
    return redirect(url_for('user_profile'))

# Generate a unique quotation number
def generate_quotation_number():
    return f"MGT-{random.randint(100000, 999999)}"

@app.route('/fetch_items', methods=['POST'])
def fetch_items():
    data = request.get_json()
    category = data.get("category")
    capacity = data.get("capacity")

    cursor = mysql.connection.cursor()

    cursor.execute('''
        SELECT id, description, quantity, price, gst_percentage, gst_amount, total
        FROM Existing_items
        WHERE category = %s AND capacity = %s
    ''', (category, capacity))

    items = cursor.fetchall()
    cursor.close()

    # Check if no items were fetched
    if not items:
        return jsonify({"error": "No items found for this category and capacity"}), 404

    # Convert the fetched data into a list of dictionaries
    items_list = []
    for item in items:
        item_dict = {
            'id': item[0],
            'description': item[1],
            'quantity': item[2],
            'price': item[3],
            'gst_percentage': item[4],
            'gst_amount': item[5],
            'total': item[6]
        }
        items_list.append(item_dict)

    # Return the items as JSON
    return jsonify({"items": items_list})

@app.route('/dgenerate_pdf', methods=['POST'])
def dgenerate_pdf():
    data = request.get_json()

    customer_name = data['customer_name']
    customer_village = data['customer_village']
    customer_email = data['customer_email']
    customer_phone = data['customer_phone']
    total_amount = data['total_amount']
    items = data['items']
    user_id = session['userid']  

    conn = mysql.connection
    cur = conn.cursor()

    # Generate quotation number BEFORE inserting
    quotation_number = generate_quotation_number()
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Insert into Existing_quotations
    cur.execute("""
    INSERT INTO Existing_quotations 
    (user_id, customer_name, customer_village, customer_email, customer_phone, total_amount, created_at, quotation_date, quotation_number) 
    VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s)
""", (user_id, customer_name, customer_village, customer_email, customer_phone, total_amount, current_date, quotation_number))

    conn.commit()

    # Get inserted quotation ID
    quotation_id = cur.lastrowid

    # Insert items into Existing_quotation_items
    for item in items:
        cur.execute("""
            INSERT INTO Existing_quotation_items 
            (quotation_id, serial_no, description, quantity, price, gst_percentage, gst_amount, total)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (quotation_id, item['serial_no'], item['description'], item['quantity'], 
              item['price'], item['gst_percentage'], item['gst_amount'], item['total']))

    conn.commit()
    cur.close()

    # Generate PDF
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    static_folder = os.path.join(os.getcwd(), r'static\images')
    header_path = os.path.join(static_folder, 'header.png')
    footer_path = os.path.join(static_folder, 'footer.png')


    styles = getSampleStyleSheet()

    def draw_header_footer_first_page(canvas, doc):
        width, height = letter
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(270, height - 110, "QUOTATION")

    def draw_header_footer_later_pages(canvas, doc):
        width, height = letter
        try:
            canvas.drawImage(header_path, 8, height - 90, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Header image error: {e}")
        try:
            canvas.drawImage(footer_path, 6, 10, width=600, height=100, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Footer image error: {e}")

    elements.append(Spacer(1, 40)) 
    elements.append(Paragraph(f"<b>Quotation Number:</b> {quotation_number}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> {current_date}", styles['Normal']))
    elements.append(Spacer(1, 20))    

    customer_info = [
        ["To:"],
        [f"Mr{customer_name}"],
        [f"{customer_village}"],
        [f"{customer_email}"],
        [f"{customer_phone}"]
    ]

    customer_table = Table(customer_info, colWidths=[460])
    customer_table.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                                        ('ALIGN', (0, 0), (0, -1), 'LEFT')]))

    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # Item Table
    table_data = [["S. No.", "Description", "Qty", "Price", "GST (%)", "GST Amt", "Total"]]
    for item in items:
        table_data.append([str(item['serial_no']), item['description'], str(item['quantity']),
                           str(item['price']), str(item['gst_percentage']), str(item['gst_amount']),
                           str(item['total'])])

    table = Table(table_data, colWidths=[40, 180, 50, 60, 50, 70, 80])
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    grand_total_table = Table([["", "", "", "", "Grand Total:", f"{total_amount}"]], colWidths=[40, 180, 50, 60, 70, 70])
    grand_total_table.setStyle(TableStyle([('FONTNAME', (4, 0), (-1, -1), 'Helvetica-Bold'),
                                            ('ALIGN', (4, 0), (-1, -1), 'CENTER'),
                                            ('BACKGROUND', (4, 0), (-1, -1), colors.lightgrey),
                                            ('GRID', (4, 0), (-1, -1), 1, colors.black)]))

    elements.append(grand_total_table)

    pdf.build(elements, onFirstPage=draw_header_footer_first_page, onLaterPages=draw_header_footer_later_pages)


    buffer.seek(0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(buffer.read())
        generated_pdf_path = temp_pdf.name

    # Merge with company.pdf using PdfWriter
    final_writer = PdfWriter()
    company_path = os.path.join(static_folder, "company.pdf")

    # Add pages from company profile
    with open(company_path, "rb") as company_file:
        company_reader = PdfReader(company_file)
        for page in company_reader.pages:
            final_writer.add_page(page)

    # Add pages from generated quotation
    with open(generated_pdf_path, "rb") as quote_file:
        quote_reader = PdfReader(quote_file)
        for page in quote_reader.pages:
            final_writer.add_page(page)

    # Output combined PDF
    final_pdf = BytesIO()
    final_writer.write(final_pdf)
    final_pdf.seek(0)

    return send_file(final_pdf, as_attachment=True, download_name="quotation_with_profile.pdf", mimetype="application/pdf")

@app.route('/my_quotations')
def my_quotations():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')  # or show an error

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM quotations WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    user_quotations = cur.fetchall()
    cur.close()

    return render_template('my_quotations.html', quotations=user_quotations)


@app.route('/process_form', methods=['POST'])
def process_form():
    # Process form data here
    # Example:
    name = request.form.get('name')
    email = request.form.get('email')
    # Save data or perform actions as needed

    # Redirect to another page after processing
    return redirect(url_for('dashboard'))

@app.route('/admin_base')
def admin_base():
    return redirect(url_for('admin_base'))

@app.route('/admin/employee')
def admin_employee():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    
    # Get all employee created by this admin
    cur.execute("""
        SELECT u.userid, u.name, u.lastname, u.email, u.role, u.phone_number, 
               COUNT(q.id) as quotation_count
        FROM user u
        LEFT JOIN quotations q ON u.userid = q.user_id
        WHERE u.role = 'employee'
        GROUP BY u.userid
        ORDER BY u.name
    """)
    
    employee_list = []
    for row in cur.fetchall():
        employee_data = {
            'userid': row[0],
            'name': row[1],
            'lastname': row[2],
            'email': row[3],
            'role': row[4],
            'phone_number': row[5],
            'quotation_count': row[6]
        }
        employee_list.append(employee_data)
        # print (employee_list)

    return render_template('employee.html', employee=employee_list)


@app.route('/admin/employee/<int:employee_id>')
def admin_employee_detail(employee_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    cur = mysql.connection.cursor()
    
    # Get employee details
    cur.execute("""
    SELECT u.userid, u.name, u.lastname, u.email, u.role, u.phone_number,u.created_at
    FROM user u
    WHERE u.userid = %s AND u.role = 'employee'
""", (employee_id,))

    
    employee = cur.fetchone()
    if not employee:
        flash('Employee not found', 'danger')
        return redirect(url_for('admin_employee'))
    
    employee = {
    'userid': employee[0],
    'name': employee[1],
    'lastname': employee[2],
    'email': employee[3],
    'role': employee[4],
    'phone_number': employee[5],
    'created_at': employee[6].strftime('%Y-%m-%d') if employee[6] else None
}

    
    # Get quotation stats
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Accepted' THEN 1 ELSE 0 END) as accepted,
            SUM(CASE WHEN status = 'Declined' THEN 1 ELSE 0 END) as declined
        FROM quotations
        WHERE user_id = %s
    """, (employee_id,))
    stats = cur.fetchone()
    employee['quotation_count'] = stats[0]
    employee['accepted_quotations'] = stats[1]
    employee['declined_quotations'] = stats[2]
    
    # Get recent quotations
    cur.execute("""
        SELECT quotation_number, customer_name, quotation_date, total_amount, status
        FROM quotations
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (employee_id,))
    
    recent_quotations = []
    for row in cur.fetchall():
        quotation = {
            'quotation_number': row[0],
            'customer_name': row[1],
            'quotation_date': row[2].strftime('%Y-%m-%d') if row[2] else None,
            'total_amount': row[3],
            'status': row[4]
        }
        recent_quotations.append(quotation)
    
    cur.close()
    return render_template('employee_detail.html', 
                         employee=employee, 
                         recent_quotations=recent_quotations)

@app.route('/admin/employee/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    if 'admin' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    cur = mysql.connection.cursor()
    try:
        # First check if employee exists and is not an admin
        cur.execute("SELECT role FROM user WHERE userid = %s", (employee_id,))
        employee = cur.fetchone()
        
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
            
        if employee[0] == 'admin':
            return jsonify({'error': 'Cannot delete admin users'}), 400
            
        # Delete the employee
        cur.execute("DELETE FROM user WHERE userid = %s", (employee_id,))
        mysql.connection.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5032, debug=True)

