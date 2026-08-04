ALTER TABLE wowprime.brands;

UPDATE wowprime.brands
SET brand_name2 = CASE 
    -- 1. 如果名稱裡面包含空格，直接抓空格前面的文字（例如：'青花驕 麻辣鍋' -> '青花驕'）
    WHEN brand_name LIKE '% %' THEN SUBSTRING_INDEX(brand_name, ' ', 1)
    
    -- 2. 開頭是英文/數字的品牌（例如：'12mini快煮小火鍋' -> '12mini'，'TASTy西堤牛排' -> 'TASTy'）
    WHEN brand_name REGEXP '^[a-zA-Z0-9]+' THEN REGEXP_SUBSTR(brand_name, '^[a-zA-Z0-9]+')
    
    -- 3. 其他純中文且無空格的品牌，統一截取前 2 個字（例如：'陶板屋和風洋食' -> '陶板屋'、'品田牧場' -> '品田'）
    ELSE LEFT(brand_name, 2)
END;