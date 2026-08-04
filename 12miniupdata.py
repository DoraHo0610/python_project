#####################################################
# store-12mini
#####################################################

import getpass
import os
import re
import bs4
import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 載入 .env 設定
load_dotenv("./.env", override=True)


# ==========================================
# 0. 共用工具函式 (地址拆解)
# ==========================================
def parse_address_info(address: str):
    if not address:
        return None, None
    match = re.match(r"^(.{2}[縣市])(.{1,4}[鄉鎮市區])", address.strip())
    if match:
        return match.group(1), match.group(2)
    elif len(address) >= 3:
        return address[:3], None
    return None, None


# ==========================================
# 1. 各品牌專屬爬蟲函式區
# ==========================================


# --- [品牌 13] 12MINI 快煮小火鍋 ---
def scrape_12mini(brand_id: int):
    brand_name = "12MINI"
    url = "https://www.12mini.com.tw/store.php"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    stores = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = "utf-8"
        soup = bs4.BeautifulSoup(res.text, "html.parser")

        # 1. 定位所有門市卡片 div.card--store
        cards = soup.select("div.card--store")

        for card in cards:
            # 2. 分店名稱 (div.caption__title)
            name_el = card.select_one("div.caption__title")
            store_name = name_el.text.strip() if name_el else ""

            # 3. 電話 (a.contect__phone 或 a[href^='tel:'])
            phone_el = card.select_one("a.contect__phone, a[href^='tel:']")
            phone = phone_el.text.strip() if phone_el else ""

            # 4. 精準拆解所有 content__desc 區塊 (地址 vs 營業時間)
            address = ""
            business_hours = "詳見官網"

            desc_list = card.select("div.content__desc")

            hours_texts = []
            for desc in desc_list:
                txt = desc.text.strip()
                if not txt:
                    continue

                # 判斷 A：若為電話號碼則忽略
                if desc.select_one("a[href^='tel:']") or re.search(
                    r"\d{2,4}-\d{6,8}", txt
                ):
                    continue

                # 判斷 B：如果包含縣市名稱 (如 台北市、新北市、台中市等)，明確判定為地址
                if not address and re.search(
                    r"^.{2,3}[縣市].{1,4}[鄉鎮市區]", txt
                ):
                    address = txt
                    continue

                # 判斷 C：其餘區塊 (如包含 週一~週日、時間 11:00-21:30 等) 歸類為營業時間
                if (
                    "週" in txt
                    or ":" in txt
                    or "點" in txt
                    or "時間" in txt
                    or "最後" in txt
                ):
                    hours_texts.append(txt)

            if hours_texts:
                business_hours = " ".join(hours_texts)

            # 5. 外帶點餐連結 (替代 booking_url)
            takeout_el = card.select_one(
                "a[ga-label='外帶點餐'], a[href*='aio2.wowprime.com'],"
                " a[href*='order']"
            )
            booking_url = (
                takeout_el["href"]
                if takeout_el and takeout_el.has_attr("href")
                else None
            )

            # 6. 解析縣市與鄉鎮區 (City & District)
            city, district = parse_address_info(address)

            if store_name:
                stores.append(
                    {
                        "brand_id": brand_id,
                        "store_name": store_name,
                        "full_name": f"{brand_name} {store_name}",
                        "address": address,
                        "city": city,
                        "district": district,
                        "phone": phone,
                        "booking_url": booking_url,
                        "business_hours": business_hours,
                        "status": "營業中",
                    }
                )

        print(f"✅ 【{brand_name}】成功解析 {len(stores)} 筆門市！")

    except Exception as e:
        print(f"❌ 抓取【{brand_name}】失敗: {e}")

    return stores


# ==========================================
# 2. 主執行流程 (Main Pipeline)
# ==========================================
def main():
    # 1. MySQL 資料庫連線
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER") or input("DB user: ")
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass(
        "DB password: "
    )
    DB_NAME = os.environ.get("DB_NAME", "wowprime")

    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url)

    # 2. 撈取 brands 資料表中的品牌名單對照表
    print("🔍 正在獲取資料庫中的品牌對照資料...")
    brands_df = pd.read_sql(
        "SELECT brand_id, brand_name FROM brands;", con=engine
    )

    def get_brand_id(keyword):
        matched = brands_df[
            brands_df["brand_name"].str.contains(keyword, na=False)
        ]
        if not matched.empty:
            return int(matched.iloc[0]["brand_id"])
        return None

    all_stores = []

    # 3. 執行 12MINI 採集
    mini_id = get_brand_id("12MINI") or get_brand_id("12mini")
    mini_stores = scrape_12mini(brand_id=mini_id)
    all_stores.extend(mini_stores)

    # 4. 統一轉換成 DataFrame 並寫入 MySQL
    if all_stores:
        df_all = pd.DataFrame(all_stores)
        print(f"\n📊 總共採集到 {len(df_all)} 筆 12MINI 門市資料！")

        # 預覽前幾筆資料確認 address/city/district 是否正確解析
        print("\n👀 資料預覽 (前 3 筆)：")
        print(
            df_all[["store_name", "address", "city", "district"]].head(3)
        )

        try:
            df_all.to_sql(
                name="stores", con=engine, if_exists="append", index=False
            )
            print("\n🎉 成功將所有 12MINI 門市資料寫入 MySQL `stores` 資料表！")
        except Exception as e:
            print(f"\n❌ 資料庫匯入失敗：{e}")


if __name__ == "__main__":
    main()




#####################################################
# google_score
#####################################################
# import getpass
# import os
# import re
# import time
# from dotenv import load_dotenv
# import pandas as pd
# from sqlalchemy import create_engine, text
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait

# # ====================================================
# # 1. 載入 .env 設定並建立資料庫連線
# # ====================================================
# load_dotenv("./.env", override=True)

# DB_HOST = os.environ.get("DB_HOST", "localhost")
# DB_PORT = int(os.environ.get("DB_PORT", 3306))
# DB_USER = os.environ.get("DB_USER") or input("DB user: ")
# DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass("DB password: ")
# DB_NAME = os.environ.get("DB_NAME", "wowprime")

# engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
# engine = create_engine(engine_url)


# # ====================================================
# # 2. Google Maps 自動化爬蟲函式
# # ====================================================
# def get_google_maps_score(driver, store_full_name: str):
#     """傳入已開啟的 driver 與門市全名，回傳 (rating, review_count)"""
#     rating = None
#     review_count = None

#     try:
#         # 1. 帶入搜尋關鍵字直接連入 Google 地圖
#         encoded_query = store_full_name.replace(" ", "+")
#         search_url = f"https://www.google.com/maps/search/{encoded_query}"
#         driver.get(search_url)

#         wait = WebDriverWait(driver, 10)

#         # 2. 等待主要區塊載入
#         wait.until(
#             EC.presence_of_element_located(
#                 (By.CSS_SELECTOR, "div[role='main'], div.F7nice, h1")
#             )
#         )
#         time.sleep(1.5)

#         # 3. 若停留在搜尋結果列表頁（網址不含 /maps/place/），點擊第一個結果進入店家詳細頁
#         if "/maps/place/" not in driver.current_url:
#             try:
#                 first_card = driver.find_element(
#                     By.CSS_SELECTOR, "a.hfA2B, div.Nv2pk a"
#                 )
#                 first_card.click()
#                 time.sleep(2)
#             except Exception:
#                 pass

#         # 4. 專門等待評論數 (帶有括號或則評論的元素) 完全非同步渲染出來
#         try:
#             wait.until(
#                 lambda d: d.find_element(
#                     By.CSS_SELECTOR, "span[aria-label*='則評論']"
#                 ).get_attribute("aria-label")
#                 or "(" in d.find_element(By.CSS_SELECTOR, "div.F7nice").text
#             )
#         except Exception:
#             time.sleep(1.5)  # 若等待超時，額外給予緩衝時間

#         time.sleep(1)  # 確保動態文字渲染完全

#         # ----------------------------------------------------
#         # 5. 抓取星等評分 (例如: 4.8)
#         # ----------------------------------------------------
#         try:
#             f7_el = driver.find_element(By.CSS_SELECTOR, "div.F7nice")
#             f7_spans = f7_el.find_elements(By.CSS_SELECTOR, "span")
#             for s in f7_spans:
#                 txt = s.text.strip()
#                 if re.match(r"^[1-5]\.\d$", txt):
#                     rating = float(txt)
#                     break
#         except Exception:
#             pass

#         # ----------------------------------------------------
#         # 6. 精準抓取評論次數 (例如: 23299)
#         # ----------------------------------------------------
#         # 策略 A：依據 aria-label="23,299 則評論" 或純文字 "(23,299)" 擷取純數字
#         try:
#             rev_spans = driver.find_elements(
#                 By.CSS_SELECTOR,
#                 "div.F7nice span[aria-label*='則評論'],"
#                 " span[aria-label*='則評論']",
#             )
#             for rev_el in rev_spans:
#                 aria_txt = rev_el.get_attribute("aria-label") or ""
#                 inner_txt = rev_el.text.strip()

#                 match = re.search(r"([\d,]+)\s*則評論", aria_txt) or re.search(
#                     r"\(([\d,]+)\)", inner_txt
#                 )
#                 if match:
#                     review_count = int(match.group(1).replace(",", ""))
#                     break
#         except Exception:
#             pass

#         # 策略 B (備用)：從 div.F7nice 完整純文字提取括號內的數字
#         if review_count is None:
#             try:
#                 f7_text = driver.find_element(
#                     By.CSS_SELECTOR, "div.F7nice"
#                 ).text
#                 match = re.search(r"\(([\d,]+)\)", f7_text)
#                 if match:
#                     review_count = int(match.group(1).replace(",", ""))
#             except Exception:
#                 pass

#     except Exception as e:
#         print(f"⚠️ 爬取 [{store_full_name}] 發生異常: {e}")

#     return rating, review_count


# # ====================================================
# # 3. 主流程：從 DB 讀取門市 -> 批次爬取 -> 回寫 DB
# # ====================================================
# def main():
#     # Chrome 瀏覽器啟動設定
#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")  # 全自動批次跑時，若不希望看到視窗可開啟此行
#     chrome_options.add_argument("--lang=zh-TW")
#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#         " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     )

#     # 1. 從資料庫讀取所有門市資料
#     print("🔍 正在連線資料庫並讀取門市資料...")
#     query = "SELECT store_id, full_name FROM stores WHERE status = '營業中' AND brand_id = 14;"

#     try:
#         stores_df = pd.read_sql(query, engine)
#         print(f"✅ 成功獲取 {len(stores_df)} 筆門市資料！\n")
#     except Exception as e:
#         print(f"❌ 讀取資料庫失敗，請檢查 SQL 連線與 .env 設定: {e}")
#         return

#     if stores_df.empty:
#         print("⚠️ 無待處理門市資料！")
#         return

#     # 2. 啟動瀏覽器進行批次爬取與即時回寫
#     driver = webdriver.Chrome(options=chrome_options)

#     # SQL 更新語句
#     update_sql = text("""
#         UPDATE stores 
#         SET google_rating = :rating, 
#             google_review_count = :review_count
#         WHERE store_id = :store_id
#     """)

#     success_count = 0

#     try:
#         # 使用 SQLAlchemy 交易 (Transaction) 機制，確保自動 commit
#         with engine.begin() as conn:
#             for idx, row in stores_df.iterrows():
#                 store_id = row["store_id"]
#                 full_name = row["full_name"]

#                 print(
#                     f"[{idx+1}/{len(stores_df)}] 正在處理: {full_name} ..."
#                 )

#                 # 執行 Google Maps 爬蟲
#                 rating, review_count = get_google_maps_score(driver, full_name)

#                 # 即時寫回資料庫
#                 conn.execute(
#                     update_sql,
#                     {
#                         "rating": rating,
#                         "review_count": review_count,
#                         "store_id": store_id,
#                     },
#                 )

#                 print(
#                     f"   ↳ 爬取成功: 評分={rating} | 評論數={review_count} -> 已更新至 DB"
#                 )
#                 success_count += 1

#                 # 間隔 2 秒，防範請求過於頻繁
#                 time.sleep(2)

#         print(
#             f"\n🎉 全數處理完畢！成功更新 {success_count} 筆門市數據至資料庫！"
#         )

#     except Exception as e:
#         print(f"❌ 批次更新過程發生錯誤: {e}")
#     finally:
#         driver.quit()


# if __name__ == "__main__":
#     main()





#####################################################
# google_info
#####################################################

# import getpass
# import os
# import re
# import time
# from dotenv import load_dotenv
# import pandas as pd
# from sqlalchemy import create_engine, text
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.support.ui import WebDriverWait

# # ====================================================
# # 1. 載入 .env 設定並建立資料庫連線
# # ====================================================
# load_dotenv("./.env", override=True)

# DB_HOST = os.environ.get("DB_HOST", "localhost")
# DB_PORT = int(os.environ.get("DB_PORT", 3306))
# DB_USER = os.environ.get("DB_USER") or input("DB user: ")
# DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass("DB password: ")
# DB_NAME = os.environ.get("DB_NAME", "wowprime")

# engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
# engine = create_engine(engine_url)


# # ====================================================
# # 2. 價位解析輔助函式
# # ====================================================
# def parse_price_and_avg(price_str: str):
#     """解析價位字串 (例如 "$1,600-2,000" -> "$1,600-2,000", 1800)"""
#     if not price_str:
#         return None, None

#     clean_str = price_str.strip()
#     # 提取所有數字（自動移除千分位逗號）
#     numbers = [int(n) for n in re.findall(r"\d+", clean_str.replace(",", ""))]

#     avg_price = None
#     if len(numbers) >= 2:
#         avg_price = int(sum(numbers[:2]) / 2)  # 算術平均值
#     elif len(numbers) == 1:
#         avg_price = numbers[0]

#     return clean_str, avg_price


# # ====================================================
# # 3. Google Maps 單店家資訊爬取函式
# # ====================================================
# def get_store_details(driver, store_full_name: str):
#     """查詢單家門市，抓取 (price_range, avg_price, latitude, longitude)"""
#     price_range = None
#     avg_price = None
#     latitude = None
#     longitude = None

#     try:
#         encoded_query = store_full_name.replace(" ", "+")
#         search_url = f"https://www.google.com/maps/search/{encoded_query}"
#         driver.get(search_url)

#         wait = WebDriverWait(driver, 10)

#         # 1. 等待主區塊載入
#         wait.until(
#             EC.presence_of_element_located(
#                 (By.CSS_SELECTOR, "div[role='main'], div.F7nice, h1")
#             )
#         )
#         time.sleep(2)

#         # 2. 如果停留在搜尋列表頁，自動點擊第一個項目進入詳細頁
#         try:
#             if "/maps/place/" not in driver.current_url:
#                 cards = driver.find_elements(
#                     By.CSS_SELECTOR, "a.hfA2B, div.Nv2pk a, a[href*='/maps/place/']"
#                 )
#                 if cards:
#                     cards[0].click()
#                     time.sleep(2.5)
#         except Exception:
#             pass

#         # 3. 等待 URL 跳轉包含 @緯度,經度 資訊
#         try:
#             wait.until(lambda d: "@" in d.current_url and "," in d.current_url)
#         except Exception:
#             time.sleep(1)

#         # ----------------------------------------------------
#         # 4. 精準從當前 URL 提取經緯度
#         # ----------------------------------------------------
#         current_url = driver.current_url
#         geo_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
#         if geo_match:
#             latitude = float(geo_match.group(1))
#             longitude = float(geo_match.group(2))

#         # ----------------------------------------------------
#         # 5. 抓取價位資訊 (如 $1,600-2,000 或 $200-400)
#         # ----------------------------------------------------
#         raw_price_str = ""

#         # 策略 A：搜尋包含 '$' 符號的元素
#         try:
#             price_elements = driver.find_elements(
#                 By.XPATH,
#                 "//span[contains(text(), '$')] | //div[contains(text(),"
#                 " '$')]",
#             )
#             for el in price_elements:
#                 txt = el.text.strip()
#                 if re.search(r"\$\s*[\d,]+", txt):
#                     raw_price_str = txt
#                     break
#         except Exception:
#             pass

#         # 策略 B (備用)：從主資訊容器文字提取價位格式
#         if not raw_price_str:
#             try:
#                 main_info = driver.find_element(
#                     By.CSS_SELECTOR, "div.LBgpqf, div.q3sShb, div.F7nice"
#                 ).text
#                 match = re.search(
#                     r"(\$\s*[\d,]+(?:\s*[\-\~～–—]\s*[\d,]+)?)", main_info
#                 )
#                 if match:
#                     raw_price_str = match.group(1)
#             except Exception:
#                 pass

#         # 6. 解析價位與計算平均值
#         if raw_price_str:
#             match_clean = re.search(
#                 r"(\$\s*[\d,]+(?:\s*[\-\~～–—]\s*[\d,]+)?)", raw_price_str
#             )
#             clean_price_text = (
#                 match_clean.group(1) if match_clean else raw_price_str
#             )
#             price_range, avg_price = parse_price_and_avg(clean_price_text)

#     except Exception as e:
#         print(f"⚠️ 抓取 [{store_full_name}] 發生異常: {e}")

#     return price_range, avg_price, latitude, longitude


# # ====================================================
# # 4. 主流程：從 DB 讀取門市 -> 批次爬取 -> 回寫 DB
# # ====================================================
# def main():
#     chrome_options = Options()
#     # chrome_options.add_argument("--headless")  # 穩定後若不需跳出瀏覽器視窗，可開啟無頭模式
#     chrome_options.add_argument("--lang=zh-TW")
#     chrome_options.add_argument(
#         "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#         " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     )

#     # 1. 連線資料庫撈取所有門市
#     print("🔍 正在連線資料庫並讀取門市資料...")
#     query = "SELECT store_id, full_name FROM stores WHERE status = '營業中' AND brand_id = 14;"

#     try:
#         stores_df = pd.read_sql(query, engine)
#         print(f"✅ 成功獲取 {len(stores_df)} 筆門市資料！\n")
#     except Exception as e:
#         print(f"❌ 讀取資料庫失敗，請檢查 SQL 連線與 .env 設定: {e}")
#         return

#     if stores_df.empty:
#         print("⚠️ 無待處理門市資料！")
#         return

#     driver = webdriver.Chrome(options=chrome_options)

#     # 資料庫 UPDATE 語句 (請確認 DB 欄位名稱是否為 latitude 與 longitude)
#     update_sql = text("""
#         UPDATE stores 
#         SET price_range = :price_range, 
#             avg_price = :avg_price,
#             latitude = :latitude,
#             longitude = :longitude
#         WHERE store_id = :store_id
#     """)

#     success_count = 0

#     try:
#         # 使用 SQLAlchemy Transaction 機制自動 commit
#         with engine.begin() as conn:
#             for idx, row in stores_df.iterrows():
#                 store_id = row["store_id"]
#                 full_name = row["full_name"]

#                 print(
#                     f"[{idx+1}/{len(stores_df)}] 正在查詢: {full_name} ..."
#                 )

#                 # 爬取價位、均價與經緯度
#                 price_range, avg_price, lat, lng = get_store_details(
#                     driver, full_name
#                 )

#                 # 即時寫回資料庫
#                 conn.execute(
#                     update_sql,
#                     {
#                         "price_range": price_range,
#                         "avg_price": avg_price,
#                         "latitude": lat,
#                         "longitude": lng,
#                         "store_id": store_id,
#                     },
#                 )

#                 print(
#                     f"   ↳ 寫入 DB: 價位={price_range} | 均價={avg_price} | 緯度={lat} | 經度={lng}"
#                 )
#                 success_count += 1

#                 time.sleep(2)  # 適度停頓避免請求過度頻繁

#         print(
#             f"\n🎉 全數門市處理完畢！成功更新 {success_count} 筆經緯度與價位數據至資料庫！"
#         )

#     except Exception as e:
#         print(f"❌ 批次更新過程發生錯誤: {e}")
#     finally:
#         driver.quit()


# if __name__ == "__main__":
#     main()