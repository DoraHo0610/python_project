import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_google_maps_score(driver, store_full_name: str):
    """傳入已開啟的 driver 與門市全名，回傳 (rating, review_count)"""
    rating = None
    review_count = None

    try:
        # 1. 帶入搜尋關鍵字
        encoded_query = store_full_name.replace(" ", "+")
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        driver.get(search_url)

        wait = WebDriverWait(driver, 10)

        # 2. 等待主面板出現
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='main'], div.F7nice, h1")
            )
        )
        time.sleep(3)

        # 3. 判斷是否停留在搜尋結果清單頁（網址不含 /maps/place/）
        if "/maps/place/" not in driver.current_url:
            print("  ℹ️ 偵測到搜尋列表，點擊第一筆進入詳細頁...")
            try:
                first_card = driver.find_element(
                    By.CSS_SELECTOR, "a.hfA2B, div.Nv2pk a"
                )
                first_card.click()
                time.sleep(2)
            except Exception as e_click:
                print(f"  ⚠️ 點擊失敗: {e_click}")

        # 4. 【關鍵修復】專門等待評論數 (帶有括號或則評論的元素) 完全渲染出來
        try:
            wait.until(
                lambda d: d.find_element(
                    By.CSS_SELECTOR, "span[aria-label*='則評論']"
                ).get_attribute("aria-label")
                or "(" in d.find_element(By.CSS_SELECTOR, "div.F7nice").text
            )
        except Exception:
            time.sleep(3)  # 若等待超時，再給予緩衝時間

        time.sleep(3)  # 確保文字渲染完全

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
        except Exception as e_rating:
            print(f"  ⚠️ 評分抓取異常: {e_rating}")

        # ----------------------------------------------------
        # 6. 精準抓取評論次數 (例如: 23299)
        # ----------------------------------------------------
        # 策略 A：直接對準 aria-label 包含 "則評論" 的標籤 (如 aria-label="23,299 則評論")
        try:
            rev_spans = driver.find_elements(
                By.CSS_SELECTOR,
                "div.F7nice span[aria-label*='則評論'],"
                " span[aria-label*='則評論']",
            )
            for rev_el in rev_spans:
                aria_txt = rev_el.get_attribute("aria-label") or ""
                inner_txt = rev_el.text.strip()

                # 從 "23,299 則評論" 或 "(23,299)" 擷取純數字
                match = re.search(r"([\d,]+)\s*則評論", aria_txt) or re.search(
                    r"\(([\d,]+)\)", inner_txt
                )
                if match:
                    review_count = int(match.group(1).replace(",", ""))
                    break
        except Exception as e_rev:
            print(f"  ⚠️ 評論次數策略 A 異常: {e_rev}")

        # 策略 B (備用)：直接從 div.F7nice 的完整純文字提取括號內的數字，如 "(23,299)"
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
        print(f"❌ 處理 [{store_full_name}] 發生未預期錯誤: {e}")

    return rating, review_count


def main():
    test_stores = [
        "肉次方 燒肉放題 台北峨嵋店",
        "夏慕尼 台北南昌店",
        "藝奇 台北南京東店",
        "肉次方 台北南京東店",
    ]

    print("🚀 開始執行 3 家門市 Google 地圖評分爬蟲測試...\n" + "=" * 50)

    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 測試階段建議保持視窗開啟觀察
    chrome_options.add_argument("--lang=zh-TW")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=chrome_options)
    results = []

    try:
        for idx, store in enumerate(test_stores, 1):
            print(f"[{idx}/{len(test_stores)}] 正在搜尋: {store}")

            rating, review_count = get_google_maps_score(driver, store)

            print(
                f"   ➔ 評分: {rating if rating is not None else '抓取失敗'}"
            )
            print(
                f"   ➔ 評論數: {review_count if review_count is not None else '抓取失敗'}"
            )
            print("-" * 50)

            results.append(
                {
                    "full_name": store,
                    "google_rating": rating,
                    "google_review_count": review_count,
                }
            )

            time.sleep(2)

        df = pd.DataFrame(results)
        print("\n📊 終端機測試結果彙整表：")
        print("=" * 50)
        print(df.to_string(index=False))
        print("=" * 50)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()