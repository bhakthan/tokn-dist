-- Synthetic insurance claims data. Fictional policies, claims and payments.
CREATE TABLE policies (
  policy_id    TEXT PRIMARY KEY,
  product_line TEXT NOT NULL,
  region_code  TEXT NOT NULL
);
CREATE TABLE claims (
  claim_id       TEXT PRIMARY KEY,
  policy_id      TEXT NOT NULL REFERENCES policies(policy_id),
  claim_status   TEXT NOT NULL,
  loss_date      TEXT NOT NULL,
  reserve_amount REAL NOT NULL
);
CREATE TABLE claim_payments (
  payment_id  TEXT PRIMARY KEY,
  claim_id    TEXT NOT NULL REFERENCES claims(claim_id),
  paid_amount REAL NOT NULL,
  paid_date   TEXT NOT NULL
);

INSERT INTO policies VALUES
  ('P-100', 'AUTO',       'NE'),
  ('P-101', 'HOME',       'SW'),
  ('P-102', 'AUTO',       'SW'),
  ('P-103', 'COMMERCIAL', 'NE'),
  ('P-104', 'HOME',       'NE');

-- Five OPEN claims: C-01..C-05. C-04 has no payments yet.
INSERT INTO claims VALUES
  ('C-01', 'P-100', 'OPEN',   '2026-03-02', 12000),
  ('C-02', 'P-101', 'OPEN',   '2026-04-11', 48000),
  ('C-03', 'P-102', 'OPEN',   '2026-05-20',  6500),
  ('C-04', 'P-103', 'OPEN',   '2026-06-07', 90000),
  ('C-05', 'P-104', 'OPEN',   '2026-07-15', 15500),
  ('C-06', 'P-100', 'CLOSED', '2025-11-03',     0),
  ('C-07', 'P-101', 'CLOSED', '2025-12-19',     0),
  ('C-08', 'P-103', 'DENIED', '2026-01-25',     0),
  ('C-09', 'P-102', 'CLOSED', '2026-02-08',     0),
  ('C-10', 'P-104', 'DENIED', '2026-02-27',     0);

INSERT INTO claim_payments VALUES
  ('PM-01', 'C-01',  2500, '2026-03-20'),
  ('PM-02', 'C-01',  1800, '2026-04-18'),
  ('PM-03', 'C-02', 10000, '2026-04-30'),
  ('PM-04', 'C-02',  7500, '2026-05-29'),
  ('PM-05', 'C-02',  4200, '2026-06-26'),
  ('PM-06', 'C-03',  3100, '2026-06-10'),
  ('PM-07', 'C-05',  2000, '2026-08-01'),
  ('PM-08', 'C-05',  2750, '2026-08-29'),
  ('PM-09', 'C-06',  5400, '2025-12-01'),
  ('PM-10', 'C-07',  8800, '2026-01-14'),
  ('PM-11', 'C-09',  1200, '2026-02-20');
