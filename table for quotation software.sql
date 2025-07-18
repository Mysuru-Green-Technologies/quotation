-- User table
CREATE TABLE IF NOT EXISTS user (
    userid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone_number VARCHAR(15),
    password VARCHAR(100) NOT NULL
);

-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    device_id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    project_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (email) REFERENCES user(email) ON DELETE CASCADE
);

-- Quotations table
CREATE TABLE IF NOT EXISTS quotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_number VARCHAR(20),
    customer_name VARCHAR(100) NOT NULL,
    customer_village VARCHAR(100),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(15),
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Draft',
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_updated DATETIME ON UPDATE CURRENT_TIMESTAMP,
    quotation_date DATE,
    revision_of INT NULL,
    FOREIGN KEY (revision_of) REFERENCES quotations(id)
);

-- Quotation items table
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
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

-- Quotation tracking table
CREATE TABLE IF NOT EXISTS quotation_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    details TEXT,
    event_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

-- Quotation reminders table
CREATE TABLE IF NOT EXISTS quotation_reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_id INT NOT NULL,
    reminder_date DATE NOT NULL,
    reminder_type VARCHAR(100) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE
);

-- Existing items table (for template items)
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
);

-- Existing quotations table
CREATE TABLE IF NOT EXISTS Existing_quotations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quotation_number VARCHAR(20) NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_village VARCHAR(100),
    customer_email VARCHAR(100),
    customer_phone VARCHAR(15),
    total_amount DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    quotation_date DATE
);

-- Existing quotation items table
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
);




