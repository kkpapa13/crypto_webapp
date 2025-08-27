DROP TABLE IF EXISTS coins;
DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS wallets;




CREATE TABLE coins (
  coin_id TEXT PRIMARY KEY,
  name TEXT NOT NULL
);

INSERT INTO coins VALUES ('ETH', 'Ethereum');
INSERT INTO coins VALUES ('BTC', 'Bitcoin');
INSERT INTO coins VALUES ('SOL', 'Solana');

CREATE TABLE trades (
  trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
  coin_id TEXT,
  trade_type TEXT,
  price REAL,
  amount REAL,
  take_profit REAL,  -- 新增止盈字段
  stop_loss REAL,
  trade_time TEXT DEFAULT CURRENT_TIMESTAMP,
  note TEXT,
  FOREIGN KEY (coin_id) REFERENCES coins(coin_id)
);

CREATE TABLE wallets (
  coin_id TEXT PRIMARY KEY,
  total_amount REAL DEFAULT 0,
  avg_cost REAL DEFAULT 0,
  FOREIGN KEY (coin_id) REFERENCES coins(coin_id)
);


