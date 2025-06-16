-- 若存在就刪除，避免重複建立錯誤
-- DROP TABLE IF EXISTS exchange_rates;
-- TRUNCATE TABLE exchange_rate_analysis;

-- 原始匯率資料表
CREATE TABLE IF NOT EXISTS exchange_rates (
    date DATE,
    base VARCHAR(10),
    currency VARCHAR(10),
    rate FLOAT,
    inverse_rate FLOAT
);

-- 分析後資料表（包含移動平均、波動率、Z-score 等）
CREATE TABLE exchange_rate_analysis (
    date DATE,
    currency TEXT,
    rate DOUBLE PRECISION,
    prev_rate DOUBLE PRECISION,
    change_percent DOUBLE PRECISION,
    moving_avg_7d DOUBLE PRECISION,
    volatility_7d DOUBLE PRECISION,
    z_score DOUBLE PRECISION
);
