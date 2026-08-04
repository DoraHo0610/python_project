DELETE FROM wowprime.stores
WHERE brand_id = 14;

-- --------------------
SELECT * FROM wowprime.stores
WHERE city='嘉義市';

UPDATE wowprime.stores
SET 
    city = '嘉義縣',
    address = REPLACE(address, '嘉義市', '嘉義縣')
WHERE city = '嘉義市';


-- --------------------
SELECT * FROM wowprime.stores
WHERE city='南投市';

-- --------------------
SELECT * FROM wowprime.stores
WHERE city='宜蘭市';
-- --------------------
SELECT * FROM wowprime.stores
WHERE city='屏東市';
-- --------------------
SELECT * FROM wowprime.stores
WHERE city='斗六市';
-- --------------------
SELECT * FROM wowprime.stores
WHERE city='彰化市';
-- --------------------
SELECT * FROM wowprime.stores
WHERE district is Null;

-- --------------------


SELECT * FROM wowprime.stores
WHERE booking_url IS NULL;


SELECT * FROM wowprime.stores
WHERE phone IS NULL;


SELECT * FROM wowprime.stores
WHERE google_review_count==0;

SELECT * FROM wowprime.stores
WHERE google_rating IS null;


SELECT * FROM wowprime.stores
WHERE latitude IS null;


SELECT * FROM wowprime.stores
WHERE avg_price IS null;


UPDATE wowprime.stores
SET 
    city = REPLACE(city, '台', '臺'),
    address = REPLACE(address, '台', '臺')
WHERE city LIKE '%台%' OR address LIKE '%台%';



SELECT full_name, city, google_rating, google_review_count, latitude, longitude, updated_at
FROM wowprime.stores;


SELECT * FROM wowprime.stores
WHERE brand_id=13;
