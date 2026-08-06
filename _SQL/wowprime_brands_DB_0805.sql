-- --------------------------------------------------------
-- 主機:                           127.0.0.1
-- 伺服器版本:                        8.0.46 - MySQL Community Server - GPL
-- 伺服器作業系統:                      Win64
-- HeidiSQL 版本:                  12.12.0.7122
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- 傾印 wowprime 的資料庫結構
CREATE DATABASE IF NOT EXISTS `wowprime` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `wowprime`;

-- 傾印  資料表 wowprime.brands 結構
CREATE TABLE IF NOT EXISTS `brands` (
  `brand_id` int NOT NULL AUTO_INCREMENT COMMENT '品牌ID',
  `brand_name` varchar(100) NOT NULL COMMENT '品牌名稱',
  `brand_name2` varchar(50) DEFAULT NULL,
  `total_stores` int DEFAULT NULL COMMENT '目前店數',
  `established_year` int DEFAULT NULL COMMENT '成立年份',
  `product_type` varchar(100) DEFAULT NULL COMMENT '產品類型',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取時間',
  PRIMARY KEY (`brand_id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 正在傾印表格  wowprime.brands 的資料：~22 rows (近似值)
INSERT INTO `brands` (`brand_id`, `brand_name`, `brand_name2`, `total_stores`, `established_year`, `product_type`, `created_at`) VALUES
	(1, '原燒 日式燒肉', '原燒', 12, 2004, '燒肉料理', '2026-07-22 08:35:13'),
	(2, '王品牛排', '王品', 11, 1993, '歐美料理', '2026-07-22 08:35:13'),
	(3, '聚 日式鍋物', '聚', 31, 2004, '鍋物料理', '2026-07-22 08:35:13'),
	(4, '藝奇日式料理', '藝奇', 9, 2005, '日韓料理', '2026-07-22 08:35:13'),
	(5, '夏慕尼 新香榭鐵板燒', '夏慕尼', 15, 2005, '鐵板燒料理', '2026-07-22 08:35:13'),
	(6, 'TASTy西堤牛排', 'TASTy', 37, 2001, '歐美料理', '2026-07-22 08:35:13'),
	(7, '陶板屋和風洋食', '陶板', 34, 2002, '日韓料理', '2026-07-22 08:35:13'),
	(8, '品田牧場', '品田', 22, 2007, '日韓料理', '2026-07-22 08:35:13'),
	(9, '石二鍋', '石二鍋', 97, 2009, '鍋物料理', '2026-07-22 08:35:13'),
	(10, '莆田', '莆田', 3, 2015, '中台式料理', '2026-07-22 08:35:13'),
	(11, '青花驕 麻辣鍋', '青花驕', 15, 2018, '鍋物料理', '2026-07-22 08:35:13'),
	(12, '享鴨 烤鴨與中華料理', '享鴨', 10, 2018, '中台式料理', '2026-07-22 08:35:13'),
	(13, '丰禾台味風格料理', '丰禾', 2, 2019, '中台式料理', '2026-07-22 08:35:13'),
	(14, '12mini快煮小火鍋', '12mini', 24, 2018, '鍋物料理', '2026-07-22 08:35:13'),
	(15, '和牛涮 日式鍋物放題', '和牛涮', 17, 2020, '鍋物料理', '2026-07-22 08:35:13'),
	(16, '尬鍋 台式潮鍋', '尬鍋', 1, 2021, '鍋物料理', '2026-07-22 08:35:13'),
	(17, '肉次方 燒肉放題', '肉次方', 12, 2021, '燒肉料理', '2026-07-22 08:35:13'),
	(18, '阪前鐵板燒', '阪前', 6, 2022, '鐵板燒料理', '2026-07-22 08:35:13'),
	(19, '就饗鐵板燒', '就饗', 5, 2023, '鐵板燒料理', '2026-07-22 08:35:13'),
	(20, '金咕 韓式原塊烤肉', '金咕', 1, 2023, '燒肉料理', '2026-07-22 08:35:13'),
	(21, '王品瘋美食購物網', '王品', 1, 2021, '零售商品料理', '2026-07-22 08:35:13'),
	(22, '王品集團', '王品', 0, NULL, '料理', '2026-07-22 08:35:13');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
