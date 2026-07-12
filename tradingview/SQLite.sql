-- SQLite
SELECT timestamp, ticker, order_action, order_contracts, order_price, open, high, low, close, volume
FROM signals
WHERE timestamp > date('now', '-1 day')
ORDER BY timestamp DESC
;



SELECT * FROM rsi WHERE timestamp > date('now', '-1 day') ORDER BY timestamp DESC;

--> count how many rows
SELECT COUNT(*) FROM rsi WHERE timestamp > date('now', '-1 day');

SELECT COUNT(*) FROM stochastic WHERE timestamp > date('now', '-1 day');


SELECT * FROM stochastic WHERE timestamp > date('now', '-1 day') ORDER BY timestamp DESC;


