
SELECT *  FROM coin_price t1 WHERE t1.interval = '1m' ORDER BY datetime asc LIMIT 10000;

SELECT *  FROM coin_price WHERE DATETIME > '2021-01-01 00:00:00' ORDER BY DATETIME desc LIMIT 10000;
SELECT COUNT(*)  FROM coin_price WHERE DATETIME > '2021-01-02 00:00:00';

SELECT *  FROM coin_price WHERE (close - open ) / open > 0.05; # 1분봉 5% 이상 상승
-- DELETE FROM coin_price WHERE DATETIME = '2021-01-02'

DELETE FROM coin_price t1 WHERE t1.interval = '1m'

SELECT *  
  FROM coin_price 
WHERE (close - open ) / OPEN < -0.01
  AND (close - open ) / OPEN > -0.03
;

SELECT *  
  FROM coin_price 
WHERE (close - open ) / OPEN > 0.01
  AND (close - open ) / OPEN < 0.05
;


#################### mysql ####################
SHOW STATUS LIKE '%pool%';
show global variables like '%max_connection%';
SHOW VARIABLES LIKE '%max_connection%'

show global variables like '%timeout';
SHOW VARIABLES LIKE '%timeout%'

SHOW PROCESSLIST 
SELECT * FROM information_schema.processlist

SET GLOBAL wait_timeout = 600
SET wait_timeout = 600



#################### RSVP ####################
SELECT COUNT(*)  FROM coin_price; -- 60000

select *
  from coin_price t1 
 where coin in ('bchusdt','btcusdt','eosusdt','ethusdt','galausdt','lunausdt','sandusdt') 
   and datetime > '2021-12-20 23:24:00' 
   and t1.interval <> '1m'  
   AND time_stamp > '2021-12-20 23:35:00' 
 order by datetime desc limit 1000
; -- 2021-12-15 13:26:27
  
SELECT *
  FROM coin_price t1 
 where coin IN ('BTCUSDT')
   AND DATETIME > '2022-01-01 00:00:00'
   AND t1.interval = '5m'  
 ORDER by datetime desc LIMIT 1000
;   
  



DELETE FROM trade_history
DELETE FROM message_history



