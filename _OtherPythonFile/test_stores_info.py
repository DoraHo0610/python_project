import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def parse_price_and_avg(price_str: str):
    """解析價位字串 (例如 "$1,600-2,000" -> "$1,600-2,000", 1800)"""
    if not price_str:
        return None, None

    clean_str = price_str.strip()
    # 提取所有數字（移除千分位逗號）
    numbers = [int(n) for n in re.findall(r"\d+", clean_str.replace(",", ""))]

    avg_price = None
    if len(numbers) >= 2:
        avg_price = int(sum(numbers[:2]) / 2)  # 算術平均值
    elif len(numbers) == 1:
        avg_price = numbers[0]

    return clean_str, avg_price


def get_store_details(driver, store_full_name: str):
    """查詢單家門市，抓取 (price_range, avg_price, latitude, longitude)"""
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
        time.sleep(3)

        # 2. 如果停留在列表頁面，嘗試點擊第一個卡片進入詳細頁
        try:
            if "/maps/place/" not in driver.current_url:
                cards = driver.find_elements(
                    By.CSS_SELECTOR, "a.hfA2B, div.Nv2pk a, a[href*='/maps/place/']"
                )
                if cards:
                    cards[0].click()
                    time.sleep(2.5)
        except Exception:
            pass

        # 3. 等待 URL 跳轉並包含 @經緯度 資訊 (最多等 8 秒)
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
        # 5. 抓取價位資訊 (如 $1,600-2,000 或 $200-400)
        # ----------------------------------------------------
        raw_price_str = ""

        # 策略 A：搜尋含有 '$' 的文字標籤
        try:
            price_elements = driver.find_elements(
                By.XPATH,
                "//span[contains(text(), '$')] | //div[contains(text(),"
                " '$')]",
            )
            for el in price_elements:
                txt = el.text.strip()
                if re.search(r"\$\s*[\d,]+", txt):
                    raw_price_str = txt
                    break
        except Exception:
            pass

        # 策略 B (備用)：從主資訊文字區塊提取價位格式
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

        # 6. 解析價位與平均數
        if raw_price_str:
            match_clean = re.search(
                r"(\$\s*[\d,]+(?:\s*[\-\~～–—]\s*[\d,]+)?)", raw_price_str
            )
            clean_price_text = (
                match_clean.group(1) if match_clean else raw_price_str
            )
            price_range, avg_price = parse_price_and_avg(clean_price_text)

    except Exception as e:
        print(f"❌ 抓取 [{store_full_name}] 發生錯誤: {e}")

    return {
        "full_name": store_full_name,
        "price_range": price_range,
        "avg_price": avg_price,
        "latitude": latitude,
        "longitude": longitude,
    }


def main():
    test_stores = [
        "王品牛排 竹北光明店",
        "原燒 頭份尚順育樂世界店",
        "陶板屋 高雄裕誠店",
    ]

    print("🚀 開始執行 3 家門市價位與經緯度爬蟲測試...\n" + "=" * 65)

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

            data = get_store_details(driver, store)

            print(
                f"   ➔ 價位區間: {data['price_range'] if data['price_range'] else '未提供/無資料'}"
            )
            print(
                f"   ➔ 平均價格: {data['avg_price'] if data['avg_price'] else '無法計算'}"
            )
            print(f"   ➔ 緯度 (Lat): {data['latitude']}")
            print(f"   ➔ 經度 (Lng): {data['longitude']}")
            print("-" * 65)

            results.append(data)
            time.sleep(2)

        df = pd.DataFrame(results)
        print("\n📊 終端機測試結果彙整表：")
        print("=" * 65)
        print(df.to_string(index=False))
        print("=" * 65)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()