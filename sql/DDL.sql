-- --------------------------------------------------------
-- 호스트:                          127.0.0.1
-- 서버 버전:                        10.5.4-MariaDB - mariadb.org binary distribution
-- 서버 OS:                        Win64
-- HeidiSQL 버전:                  11.0.0.5919
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;


-- binance 데이터베이스 구조 내보내기
CREATE DATABASE IF NOT EXISTS `binance` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `binance`;

-- 테이블 binance.backtest_history 구조 내보내기
CREATE TABLE IF NOT EXISTS `backtest_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `strategy_id` varchar(50) DEFAULT NULL,
  `datetime` datetime DEFAULT NULL,
  `trade_coin` varchar(10) NOT NULL,
  `trade_coin_price` float DEFAULT NULL,
  `trade_coin_balance` float DEFAULT NULL,
  `total_coin_price` float DEFAULT NULL,
  `total_coin_balance` float DEFAULT NULL,
  `total_usdt` float DEFAULT NULL,
  `time_stamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4862 DEFAULT CHARSET=utf8;

-- 내보낼 데이터가 선택되어 있지 않습니다.

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IF(@OLD_FOREIGN_KEY_CHECKS IS NULL, 1, @OLD_FOREIGN_KEY_CHECKS) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
