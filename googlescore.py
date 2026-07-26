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
# 2. Google Maps 自動化爬蟲函式
# ====================================================
def get_google_maps_score(driver, store_full_name: str):
    """傳入已開啟的 driver 與門市全名，回傳 (rating, review_count)"""
    rating = None
    review_count = None

    try:
        # 1. 帶入搜尋關鍵字直接連入 Google 地圖
        encoded_query = store_full_name.replace(" ", "+")
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        driver.get(search_url)

        wait = WebDriverWait(driver, 10)

        # 2. 等待主要區塊載入
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='main'], div.F7nice, h1")
            )
        )
        time.sleep(1.5)

        # 3. 若停留在搜尋結果列表頁（網址不含 /maps/place/），點擊第一個結果進入店家詳細頁
        if "/maps/place/" not in driver.current_url:
            try:
                first_card = driver.find_element(
                    By.CSS_SELECTOR, "a.hfA2B, div.Nv2pk a"
                )
                first_card.click()
                time.sleep(2)
            except Exception:
                pass

        # 4. 專門等待評論數 (帶有括號或則評論的元素) 完全非同步渲染出來
        try:
            wait.until(
                lambda d: d.find_element(
                    By.CSS_SELECTOR, "span[aria-label*='則評論']"
                ).get_attribute("aria-label")
                or "(" in d.find_element(By.CSS_SELECTOR, "div.F7nice").text
            )
        except Exception:
            time.sleep(1.5)  # 若等待超時，額外給予緩衝時間

        time.sleep(1)  # 確保動態文字渲染完全

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
        # 策略 A：依據 aria-label="23,299 則評論" 或純文字 "(23,299)" 擷取純數字
        try:
            rev_spans = driver.find_elements(
                By.CSS_SELECTOR,
                "div.F7nice span[aria-label*='則評論'],"
                " span[aria-label*='則評論']",
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

        # 策略 B (備用)：從 div.F7nice 完整純文字提取括號內的數字
        if review_count is None:
            try:
                f7_text = driver.find_element(
                    By.CSS_SELECTOR, "div.F7nice"
                ).text
                match = re.search(r"\(([\d,]+)\)", f7_text)
                if match:
                    review_count = int(match.group(1).replace(",", ""))
            except Exception:
                pass

    except Exception as e:
        print(f"⚠️ 爬取 [{store_full_name}] 發生異常: {e}")

    return rating, review_count


# ====================================================
# 3. 主流程：從 DB 讀取門市 -> 批次爬取 -> 回寫 DB
# ====================================================
def main():
    # Chrome 瀏覽器啟動設定
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 全自動批次跑時，若不希望看到視窗可開啟此行
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 1. 從資料庫讀取所有門市資料
    print("🔍 正在連線資料庫並讀取門市資料...")
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

    # 2. 啟動瀏覽器進行批次爬取與即時回寫
    driver = webdriver.Chrome(options=chrome_options)

    # SQL 更新語句
    update_sql = text("""
        UPDATE stores 
        SET google_rating = :rating, 
            google_review_count = :review_count
        WHERE store_id = :store_id
    """)

    success_count = 0

    try:
        # 使用 SQLAlchemy 交易 (Transaction) 機制，確保自動 commit
        with engine.begin() as conn:
            for idx, row in stores_df.iterrows():
                store_id = row["store_id"]
                full_name = row["full_name"]

                print(
                    f"[{idx+1}/{len(stores_df)}] 正在處理: {full_name} ..."
                )

                # 執行 Google Maps 爬蟲
                rating, review_count = get_google_maps_score(driver, full_name)

                # 即時寫回資料庫
                conn.execute(
                    update_sql,
                    {
                        "rating": rating,
                        "review_count": review_count,
                        "store_id": store_id,
                    },
                )

                print(
                    f"   ↳ 爬取成功: 評分={rating} | 評論數={review_count} -> 已更新至 DB"
                )
                success_count += 1

                # 間隔 2 秒，防範請求過於頻繁
                time.sleep(2)

        print(
            f"\n🎉 全數處理完畢！成功更新 {success_count} 筆門市數據至資料庫！"
        )

    except Exception as e:
        print(f"❌ 批次更新過程發生錯誤: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()