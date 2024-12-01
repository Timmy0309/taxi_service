
CREATE TABLE IF NOT EXISTS drivers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'available'
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    pickup VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    driver_id INTEGER REFERENCES drivers(id) ON DELETE SET NULL,
    order_number VARCHAR(5) NOT NULL
);

INSERT INTO drivers (name) VALUES ('Driver 1'), ('Driver 2'), ('Driver 3');
