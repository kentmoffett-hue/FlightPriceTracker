CREATE TABLE flight_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_date DATE NOT NULL,      -- e.g., '2026-08-16'
    destination VARCHAR(50) NOT NULL, -- e.g., 'Biarritz', 'Porto', 'Edinburgh'
    price_cad INT NOT NULL          -- e.g., 950
);