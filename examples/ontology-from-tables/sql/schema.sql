-- Fictional vehicle-service workshop. Portable DDL: SQLite, PostgreSQL and MySQL 8.
-- Declared keys here become "declared" evidence; the CSV copy has none, so TOKN
-- must infer the same links from the data.

CREATE TABLE customers (
  customer_id   INTEGER PRIMARY KEY,
  full_name     VARCHAR(80) NOT NULL,
  email         VARCHAR(120) NOT NULL,
  city          VARCHAR(40) NOT NULL
);

CREATE TABLE vehicles (
  vehicle_id    INTEGER PRIMARY KEY,
  customer_id   INTEGER NOT NULL,
  make          VARCHAR(40) NOT NULL,
  model         VARCHAR(40) NOT NULL,
  model_year    INTEGER NOT NULL,
  plate         VARCHAR(16) NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
);

CREATE TABLE technicians (
  technician_id INTEGER PRIMARY KEY,
  full_name     VARCHAR(80) NOT NULL,
  grade         VARCHAR(16) NOT NULL
);

CREATE TABLE work_order_status (
  status_code   VARCHAR(8) PRIMARY KEY,
  label         VARCHAR(40) NOT NULL
);

CREATE TABLE suppliers (
  supplier_id   INTEGER PRIMARY KEY,
  supplier_name VARCHAR(80) NOT NULL,
  contact_email VARCHAR(120) NOT NULL,
  country_code  CHAR(2) NOT NULL
);

CREATE TABLE parts (
  part_id       INTEGER PRIMARY KEY,
  part_name     VARCHAR(80) NOT NULL,
  unit_price    DECIMAL(10,2) NOT NULL,
  supplier_id   INTEGER NOT NULL,
  FOREIGN KEY (supplier_id) REFERENCES suppliers (supplier_id)
);

CREATE TABLE work_orders (
  work_order_id              INTEGER PRIMARY KEY,
  vehicle_id                 INTEGER NOT NULL,
  status_code                VARCHAR(8) NOT NULL,
  opened_on                  DATE NOT NULL,
  closed_on                  DATE NULL,
  assigned_technician_id     INTEGER NOT NULL,
  inspected_by_technician_id INTEGER NULL,
  FOREIGN KEY (vehicle_id) REFERENCES vehicles (vehicle_id),
  FOREIGN KEY (status_code) REFERENCES work_order_status (status_code),
  FOREIGN KEY (assigned_technician_id) REFERENCES technicians (technician_id),
  FOREIGN KEY (inspected_by_technician_id) REFERENCES technicians (technician_id)
);

CREATE TABLE work_order_parts (
  work_order_id INTEGER NOT NULL,
  part_id       INTEGER NOT NULL,
  PRIMARY KEY (work_order_id, part_id),
  FOREIGN KEY (work_order_id) REFERENCES work_orders (work_order_id),
  FOREIGN KEY (part_id) REFERENCES parts (part_id)
);

-- A staging extract with no declared keys: TOKN should recognise it as a
-- variant of work_orders, not a new concept.
CREATE TABLE stg_work_orders (
  work_order_id INTEGER,
  vehicle_id    INTEGER,
  status_code   VARCHAR(8),
  opened_on     DATE
);
