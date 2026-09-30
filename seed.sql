CREATE TABLE tickets (
  id         serial PRIMARY KEY,
  customer   text NOT NULL,
  subject    text NOT NULL,
  priority   text NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
  status     text NOT NULL DEFAULT 'open',
  created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO tickets (customer, subject, priority, status) VALUES
  ('acme',    'Login page returns 500',        'high',   'open'),
  ('acme',    'Export to CSV is slow',         'medium', 'open'),
  ('globex',  'Invoice total off by one cent', 'high',   'open'),
  ('globex',  'Dark mode contrast too low',    'low',    'closed'),
  ('initech', 'Webhook retries never stop',    'high',   'open'),
  ('initech', 'Typo on pricing page',          'low',    'open');
