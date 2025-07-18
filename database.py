import pymysql

# Connect to MySQL
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='userre',
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
    password VARCHAR(100) NOT NULL
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

# --- Show all tables ---
cur.execute("SHOW TABLES")
print("\n✅ Tables created in 'userre':")
for table in cur.fetchall():
    print(" -", table[0])

# --- Close connection ---
cur.close()
conn.close()
print("\n✅ All tables created with full schema in a single step.")
