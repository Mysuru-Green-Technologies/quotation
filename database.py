import pymysql

# Connect to MySQL
conn = pymysql.connect(
    host='192.168.0.174',
    user='remote_control',
    password='Remote_control',
    database='quotation_data',
    autocommit=True
)

cur = conn.cursor()

# --- USER TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS user (
    userid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(15),
    password VARCHAR(100) NOT NULL,
    role VARCHAR(50)NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    department VARCHAR(100)                  
)
""")

# --- QUOTATIONS TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS quotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_number VARCHAR(20),
    customer_name VARCHAR(100) NOT NULL,
    customer_village VARCHAR(100),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(15),
    total_amount DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    quotation_date DATE,
    user_id INT NOT NULL,
    version VARCHAR(10) DEFAULT 'V1.0',
    status ENUM('Draft', 'Sent', 'Accepted', 'Declined', 'Revised') DEFAULT 'Draft',
    follow_up_date DATE,
    outcome ENUM('Pending', 'Won', 'Lost', 'Negotiating') DEFAULT 'Pending',
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    revision_of INT,
    notes TEXT,
    FOREIGN KEY (revision_of) REFERENCES quotations(id)
)
""")

# --- QUOTATION ITEMS TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS quotation_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    serial_no INT,
    description TEXT NOT NULL,
    quantity INT,
    price DECIMAL(10,2),
    gst_percentage DECIMAL(5,2),
    gst_amount DECIMAL(10,2),
    total DECIMAL(10,2),
    is_as_per_actuals BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
)
""")

# --- QUOTATION TRACKING TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS quotation_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    event_type ENUM('Created', 'Sent', 'Followed Up', 'Revised', 'Status Changed', 'Outcome Changed') NOT NULL,
    event_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    user_id INT,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
)
""")

# --- QUOTATION REMINDERS TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS quotation_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    reminder_date DATE NOT NULL,
    reminder_type ENUM('Follow Up', 'Revision Due', 'Payment Due') NOT NULL,
    status ENUM('Pending', 'Completed', 'Snoozed') DEFAULT 'Pending',
    notes TEXT,
    user_id INT NOT NULL,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
)
""")

# --- EXISTING ITEMS TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS Existing_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    capacity VARCHAR(100),
    description TEXT NOT NULL,
    quantity INT,
    price DECIMAL(10,2),
    gst_percentage DECIMAL(5,2),
    gst_amount DECIMAL(10,2),
    total DECIMAL(10,2)
)
""")

# --- EXISTING QUOTATIONS TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS Existing_quotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_number VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_village VARCHAR(100),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(15),
    total_amount DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    quotation_date DATE,
    user_id INT NOT NULL
)
""")

# --- EXISTING QUOTATION ITEMS TABLE ---
cur.execute("""
CREATE TABLE IF NOT EXISTS Existing_quotation_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    serial_no INT,
    description TEXT NOT NULL,
    quantity INT,
    price DECIMAL(10,2),
    gst_percentage DECIMAL(5,2),
    gst_amount DECIMAL(10,2),
    total DECIMAL(10,2),
    FOREIGN KEY (quotation_id) REFERENCES Existing_quotations(id) ON DELETE CASCADE
)
""")
# -- Customers table
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    postal_code VARCHAR(20),
    tax_id VARCHAR(50),
    website VARCHAR(100),
    status ENUM('active', 'inactive', 'lead', 'prospect') DEFAULT 'lead',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES user(userid)
)
""")

# -- Customer notes table
cur.execute("""
CREATE TABLE IF NOT EXISTS customer_notes (
    note_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    user_id INT NOT NULL,
    note_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (user_id) REFERENCES user(userid)
)
""")

# -- Follow-ups/reminders table
cur.execute("""
CREATE TABLE IF NOT EXISTS customer_followups (
    followup_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    user_id INT NOT NULL,
    followup_date DATETIME NOT NULL,
    followup_type ENUM('call', 'email', 'meeting', 'other') NOT NULL,
    followup_notes TEXT,
    status ENUM('pending', 'completed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (user_id) REFERENCES user(userid)
)
""")

# -- Notifications table
cur.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    related_entity_type ENUM('customer', 'quotation', 'followup'),
    related_entity_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(userid)
)
""")

# --- Show all tables ---
cur.execute("SHOW TABLES")
print("\n✅ Tables created in 'userre':")
for table in cur.fetchall():
    print(" -", table[0])

# --- Close connection ---
cur.close()
conn.close()
print("\n✅ All tables created with full schema in a single step.")
