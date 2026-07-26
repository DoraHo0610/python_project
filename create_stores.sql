USE wowprime;

CREATE TABLE IF NOT EXISTS stores (
    store_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '門市ID',
    brand_id INT COMMENT '對應的品牌ID (外鍵)',
    store_name VARCHAR(100) NOT NULL COMMENT '門市分店名 (例如: 台北羅斯福店)',
    full_name VARCHAR(150) COMMENT '全名 (例如: 王品牛排 台北羅斯福店)',
    
    -- 聯絡與預約資訊
    address VARCHAR(255) COMMENT '完整地址',
    city VARCHAR(20) COMMENT '縣市 (例如: 台北市)',
    district VARCHAR(20) COMMENT '鄉鎮市區 (例如: 中正區)',
    phone VARCHAR(50) COMMENT '電話',
    booking_url TEXT COMMENT '線上預約連結',
    business_hours TEXT COMMENT '營業時間',
    status VARCHAR(20) DEFAULT '營業中' COMMENT '門市狀態 (營業中/歇業)',

    -- 消費價位資訊 (新增與優化)
    price_range VARCHAR(50) COMMENT 'Google 人均消費區間文字 (例如: NT$400-600)',
    avg_price INT COMMENT '估算平均人均消費金額 (例如: 500, 方便排序與篩選)',

    -- 地理資訊 (GIS 地圖繪製用)
    latitude DECIMAL(10, 8) COMMENT '緯度 Lat',
    longitude DECIMAL(11, 8) COMMENT '經度 Lng',

    -- 輿情與評價資訊 (分析與排序用)
    google_rating DECIMAL(2, 1) COMMENT 'Google 評分 (1.0~5.0)',
    google_review_count INT DEFAULT 0 COMMENT 'Google 評論總數',
    google_place_id VARCHAR(100) COMMENT 'Google 地圖獨有 Place ID',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '建立時間',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '資料更新時間',

    FOREIGN KEY (brand_id) REFERENCES brands(brand_id) ON DELETE SET NULL
);