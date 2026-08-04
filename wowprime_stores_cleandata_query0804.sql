SELECT * FROM wowprime.stores
WHERE address is NULL;

DELETE FROM wowprime.stores
WHERE brand_id = 14;

SELECT * FROM wowprime.stores
WHERE city='嘉義市';

SELECT * FROM wowprime.stores
WHERE city IS Null;

SELECT * FROM wowprime.stores
WHERE booking_url IS NULL;

SELECT * FROM wowprime.stores
WHERE google_review_count IS NULL;

UPDATE wowprime.stores
SET 
    city = REPLACE(city, '臺', '台'),
    address = REPLACE(address, '臺', '台')
WHERE city LIKE '%臺%' OR address LIKE '%臺%';



SELECT full_name, city, google_rating, google_review_count, latitude, longitude, updated_at
FROM wowprime.stores;


