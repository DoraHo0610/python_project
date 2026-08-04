import getpass
import os
import re
import time
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ====================================================
# 1. 載入 .env 設定並建立資料庫連線
# ====================================================
load_dotenv("./.env", override=True)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER") or input("DB user: ")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass("DB password: ")
DB_NAME = os.environ.get("DB_NAME", "wowprime")

engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(engine_url)


# ====================================================
# 2. 價位解析輔助函式
# ====================================================
def parse_price_and_avg(price_str: str):
    """解析價位字串 (例如 "$1,600-2,000" -> "$1,600-2,000", 1800)"""
    if not price_str:
        return None, None

    clean_str = price_str.strip()
    # 提取所有數字（自動移除千分位逗號）
    numbers = [int(n) for n in re.findall(r"\d+", clean_str.replace(",", ""))]

    avg_price = None
    if len(numbers) >= 2:
        avg_price = int(sum(numbers[:2]) / 2)  # 算術平均值
    elif len(numbers) == 1:
        avg_price = numbers[0]

    return clean_str, avg_price


# ====================================================
# 3. Google Maps 綜合資訊單店採集函式
# ====================================================
def get_store_google_info(driver, store_full_name: str):
    """
    查詢單家門市，一次抓取所有所需欄位：
    回傳 (rating, review_count, price_range, avg_price, latitude, longitude)
    """
    rating = None
    review_count = None
    price_range = None
    avg_price = None
    latitude = None
    longitude = None

    try:
        encoded_query = store_full_name.replace(" ", "+")
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        driver.get(search_url)

        wait = WebDriverWait(driver, 10)

        # 1. 等待主區塊載入
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='main'], div.F7nice, h1")
            )
        )
        time.sleep(1.5)

        # 2. 若停留在搜尋列表頁，點擊第一個項目進入詳細頁
        if "/maps/place/" not in driver.current_url:
            try:
                cards = driver.find_elements(
                    By.CSS_SELECTOR, "a.hfA2B, div.Nv2pk a, a[href*='/maps/place/']"
                )
                if cards:
                    cards[0].click()
                    time.sleep(2)
            except Exception:
                pass

        # 3. 等待網址跳轉包含 @緯度,經度 資訊 (最多等 3 秒)
        try:
            wait.until(lambda d: "@" in d.current_url and "," in d.current_url)
        except Exception:
            time.sleep(1)

        # ----------------------------------------------------
        # 4. 精準從當前 URL 提取經緯度
        # ----------------------------------------------------
        current_url = driver.current_url
        geo_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
        if geo_match:
            latitude = float(geo_match.group(1))
            longitude = float(geo_match.group(2))

        # ----------------------------------------------------
        # 5. 抓取星等評分 (例如: 4.8)
        # ----------------------------------------------------
        try:
            f7_el = driver.find_element(By.CSS_SELECTOR, "div.F7nice")
            f7_spans = f7_el.find_elements(By.CSS_SELECTOR, "span")
            for s in f7_spans:
                txt = s.text.strip()
                if re.match(r"^[1-5]\.\d$", txt):
                    rating = float(txt)
                    break
        except Exception:
            pass

        # ----------------------------------------------------
        # 6. 精準抓取評論次數 (例如: 23299)
        # ----------------------------------------------------
        try:
            rev_spans = driver.find_elements(
                By.CSS_SELECTOR,
                "div.F7nice span[aria-label*='則評論'], span[aria-label*='則評論']",
            )
            for rev_el in rev_spans:
                aria_txt = rev_el.get_attribute("aria-label") or ""
                inner_txt = rev_el.text.strip()

                match = re.search(r"([\d,]+)\s*則評論", aria_txt) or re.search(
                    r"\(([\d,]+)\)", inner_txt
                )
                if match:
                    review_count = int(match.group(1).replace(",", ""))
                    break
        except Exception:
            pass

        # 備用方案：從 div.F7nice 完整純文字提取括號內的數字
        if review_count is None:
            try:
                f7_text = driver.find_element(By.CSS_SELECTOR, "div.F7nice").text
                match = re.search(r"\(([\d,]+)\)", f7_text)
                if match:
                    review_count = int(match.group(1).replace(",", ""))
            except Exception:
                pass

        # ----------------------------------------------------
        # 7. 抓取價位資訊 (例如 $1,600-2,000 或 $200-400)
        # ----------------------------------------------------
        raw_price_str = ""

        # 策略 A：搜尋包含 '$' 符號的元素
        try:
            price_elements = driver.find_elements(
                By.XPATH,
                "//span[contains(text(), '$')] | //div[contains(text(), '$')]",
            )
            for el in price_elements:
                txt = el.text.strip()
                if re.search(r"\$\s*[\d,]+", txt):
                    raw_price_str = txt
                    break
        except Exception:
            pass

        # 策略 B (備用)：從主資訊容器文字提取價位格式
        if not raw_price_str:
            try:
                main_info = driver.find_element(
                    By.CSS_SELECTOR, "div.LBgpqf, div.q3sShb, div.F7nice"
                ).text
                match = re.search(
                    r"(\$\s*[\d,]+(?:\s*[\-\~～–—]\s*[\d,]+)?)", main_info
                )
                if match:
                    raw_price_str = match.group(1)
            except Exception:
                pass

        # 解析價位與計算平均值
        if raw_price_str:
            match_clean = re.search(
                r"(\$\s*[\d,]+(?:\s*[\-\~～–—]\s*[\d,]+)?)", raw_price_str
            )
            clean_price_text = (
                match_clean.group(1) if match_clean else raw_price_str
            )
            price_range, avg_price = parse_price_and_avg(clean_price_text)

    except Exception as e:
        print(f"⚠️ 抓取 [{store_full_name}] 發生異常: {e}")

    return rating, review_count, price_range, avg_price, latitude, longitude


# ====================================================
# 4. 主流程：從 DB 讀取門市 -> 批次一次抓齊 -> 一次寫回 DB
# ====================================================
def main():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 穩定後可開啟無頭模式隱藏視窗
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 1. 從資料庫連線撈取所有待查詢門市
    print("🔍 正在連線資料庫並讀取營業中門市資料...")
    query = "SELECT store_id, full_name FROM stores WHERE status = '營業中';"

    try:
        stores_df = pd.read_sql(query, engine)
        print(f"✅ 成功獲取 {len(stores_df)} 筆門市資料！\n")
    except Exception as e:
        print(f"❌ 讀取資料庫失敗，請檢查 SQL 連線與 .env 設定: {e}")
        return

    if stores_df.empty:
        print("⚠️ 無待處理門市資料！")
        return

    driver = webdriver.Chrome(options=chrome_options)

    # 整合後的單一 SQL UPDATE 語句
    update_sql = text("""
        UPDATE stores 
        SET google_rating = :rating, 
            google_review_count = :review_count,
            price_range = :price_range, 
            avg_price = :avg_price,
            latitude = :latitude,
            longitude = :longitude
        WHERE store_id = :store_id
    """)

    success_count = 0

    try:
        # 使用 Transaction 機制確保自動 commit
        with engine.begin() as conn:
            for idx, row in stores_df.iterrows():
                store_id = row["store_id"]
                full_name = row["full_name"]

                print(f"[{idx+1}/{len(stores_df)}] 正在查詢: {full_name} ...")

                # 一次採集所有欄位
                rating, rev_count, price_range, avg_price, lat, lng = (
                    get_store_google_info(driver, full_name)
                )

                # 即時一次更新所有欄位至資料庫
                conn.execute(
                    update_sql,
                    {
                        "rating": rating,
                        "review_count": rev_count,
                        "price_range": price_range,
                        "avg_price": avg_price,
                        "latitude": lat,
                        "longitude": lng,
                        "store_id": store_id,
                    },
                )

                print(
                    f"   ↳ 寫入 DB: ⭐{rating} ({rev_count}則) | 💰{price_range}(均價:{avg_price}) | 📍({lat}, {lng})"
                )
                success_count += 1

                time.sleep(2)  # 適度停頓避免請求過度頻繁

        print(
            f"\n🎉 全數門市處理完畢！成功更新 {success_count} 筆門市的綜合 Google 數據至資料庫！"
        )

    except Exception as e:
        print(f"❌ 批次更新過程發生錯誤: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()