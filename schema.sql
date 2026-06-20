-- Create Database
CREATE DATABASE IF NOT EXISTS medicine_shop;
USE medicine_shop;

-- Create Medicines Table
CREATE TABLE IF NOT EXISTS medicines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    expiry_date DATE NOT NULL
);

-- Create Sales Table
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_id INT NOT NULL,
    quantity INT NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

-- Insert Dummy Data for Medicines (Optional for testing)
INSERT INTO medicines (name, category, price, quantity, expiry_date) VALUES 
('Paracetamol', 'Painkiller', 15.00, 100, '2025-12-31'),
('Amoxicillin', 'Antibiotic', 120.00, 50, '2024-05-15'),
('Ceterizine', 'Antihistamine', 25.00, 200, '2026-08-20'),
('Napa Extend', 'Painkiller', 20.00, 5, '2023-11-10');