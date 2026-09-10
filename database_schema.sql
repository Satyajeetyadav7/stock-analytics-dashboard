-- Stock Analytics Dashboard Database Schema

CREATE TABLE IF NOT EXISTS stock_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR(10) NOT NULL,
    trade_date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    adjusted_close REAL,
    volume INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, trade_date)
);

CREATE TABLE IF NOT EXISTS technical_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR(10) NOT NULL,
    trade_date TEXT NOT NULL,
    sma_20 REAL,
    sma_50 REAL,
    ema_12 REAL,
    ema_26 REAL,
    macd REAL,
    signal_line REAL,
    rsi REAL,
    atr REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, trade_date),
    FOREIGN KEY (ticker) REFERENCES stock_data(ticker)
);

CREATE TABLE IF NOT EXISTS trading_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR(10) NOT NULL,
    signal_date TEXT NOT NULL,
    signal_type VARCHAR(20),
    confidence_score REAL,
    price_at_signal REAL,
    target_price REAL,
    stop_loss REAL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker) REFERENCES stock_data(ticker)
);

CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_name VARCHAR(255),
    ticker VARCHAR(10) NOT NULL,
    quantity REAL,
    purchase_price REAL,
    purchase_date TEXT NOT NULL,
    current_value REAL,
    gain_loss REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    added_date TEXT,
    target_price REAL,
    alert_threshold REAL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_stock_ticker ON stock_data(ticker);
CREATE INDEX IF NOT EXISTS idx_stock_date ON stock_data(trade_date);
CREATE INDEX IF NOT EXISTS idx_indicators_ticker ON technical_indicators(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_ticker ON trading_signals(ticker);
CREATE INDEX IF NOT EXISTS idx_portfolio_ticker ON portfolio(ticker);

-- VIEWS
CREATE VIEW IF NOT EXISTS v_current_stock_status AS
SELECT 
    s.ticker,
    s.close_price AS current_price,
    s.volume,
    t.rsi,
    t.macd,
    t.sma_20,
    t.sma_50,
    s.trade_date AS last_updated
FROM stock_data s
LEFT JOIN technical_indicators t ON s.ticker = t.ticker AND s.trade_date = t.trade_date
WHERE s.trade_date = (SELECT MAX(trade_date) FROM stock_data);

CREATE VIEW IF NOT EXISTS v_portfolio_summary AS
SELECT 
    portfolio_name,
    COUNT(*) AS number_of_stocks,
    SUM(current_value) AS total_portfolio_value,
    SUM(gain_loss) AS total_gain_loss,
    ROUND(SUM(gain_loss) / SUM(current_value) * 100, 2) AS total_return_percentage
FROM portfolio
GROUP BY portfolio_name;
