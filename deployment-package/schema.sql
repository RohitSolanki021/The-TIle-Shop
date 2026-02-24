-- The Tile Shop - MySQL Database Schema
-- Version: 1.0

-- Create database
CREATE DATABASE IF NOT EXISTS tileshop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tileshop;

-- Tiles table
CREATE TABLE IF NOT EXISTS tiles (
    tile_id VARCHAR(36) PRIMARY KEY,
    size VARCHAR(50) NOT NULL,
    coverage DECIMAL(10, 2) DEFAULT 0,
    box_coverage_sqft DECIMAL(10, 2) DEFAULT 0,
    box_packing INT DEFAULT 0,
    product_name VARCHAR(255),
    rate_per_sqft DECIMAL(10, 2),
    rate_per_box DECIMAL(10, 2),
    active BOOLEAN DEFAULT TRUE,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_deleted (deleted),
    INDEX idx_size (size)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT,
    gstin VARCHAR(50),
    total_pending DECIMAL(12, 2) DEFAULT 0,
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_deleted (deleted),
    INDEX idx_name (name),
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Invoices table
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,
    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),
    customer_address TEXT,
    customer_gstin VARCHAR(50),
    ship_to_name VARCHAR(255),
    ship_to_address TEXT,
    reference_name VARCHAR(255),
    remarks TEXT,
    date DATE NOT NULL,
    subtotal DECIMAL(12, 2) DEFAULT 0,
    gst_percent DECIMAL(5, 2) DEFAULT 18.00,
    gst_amount DECIMAL(12, 2) DEFAULT 0,
    transport_charges DECIMAL(10, 2) DEFAULT 0,
    unloading_charges DECIMAL(10, 2) DEFAULT 0,
    grand_total DECIMAL(12, 2) DEFAULT 0,
    amount_paid DECIMAL(12, 2) DEFAULT 0,
    pending_balance DECIMAL(12, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Draft',
    deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    INDEX idx_customer (customer_id),
    INDEX idx_deleted (deleted),
    INDEX idx_date (date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Invoice line items table
CREATE TABLE IF NOT EXISTS invoice_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id VARCHAR(50) NOT NULL,
    tile_id VARCHAR(36),
    section_name VARCHAR(100),
    product_name VARCHAR(255),
    size VARCHAR(50),
    coverage DECIMAL(10, 2) DEFAULT 0,
    box_coverage_sqft DECIMAL(10, 2) DEFAULT 0,
    rate_per_sqft DECIMAL(10, 2) DEFAULT 0,
    rate_per_box DECIMAL(10, 2) DEFAULT 0,
    box_qty INT DEFAULT 0,
    extra_sqft DECIMAL(10, 2) DEFAULT 0,
    total_sqft DECIMAL(10, 2) DEFAULT 0,
    discount_percent DECIMAL(5, 2) DEFAULT 0,
    amount_before_discount DECIMAL(12, 2) DEFAULT 0,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    final_amount DECIMAL(12, 2) DEFAULT 0,
    remarks TEXT,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    FOREIGN KEY (tile_id) REFERENCES tiles(tile_id),
    INDEX idx_invoice (invoice_id),
    INDEX idx_tile (tile_id),
    INDEX idx_section (section_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Invoice sequence table for auto-incrementing invoice numbers
CREATE TABLE IF NOT EXISTS invoice_sequence (
    financial_year VARCHAR(10) PRIMARY KEY,
    last_sequence INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admin users table (for authentication)
CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (username: Thetileshop, password: Vicky123)
-- Password hash for 'Vicky123' using PASSWORD_DEFAULT
INSERT INTO admin_users (username, password_hash) VALUES 
('Thetileshop', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi')
ON DUPLICATE KEY UPDATE username=username;

-- Note: You should change this password after first login
-- To generate new password hash in PHP: password_hash('your_password', PASSWORD_DEFAULT)
