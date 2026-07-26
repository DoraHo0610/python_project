import getpass
import os
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 載入環境變數
load_dotenv("./.env", override=True)


# ==========================================
# 工具函式：地址拆解
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
# 步驟 1：品牌資料爬蟲與寫入
# ==========================================
def process_brands(engine):
    print("\n🚀 [階段一] 開始抓取王品集團品牌資料...")
    url = "https://www.wowprime.com/zh-tw/investors-sub-menu/about-wowprime/brand-introduction/taiwan"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    brands_data = []
    cards = soup.select("div.brands-list div.wrap")

    for card in cards:
        title_tag = card.select_one("div.title")
        brand_name = title_tag.text.strip() if title_tag else "未知品牌"

        items = card.select("div.info-wrap div.item")
        branches_count = None
        established_time = None
        product_type = None

        for item in items:
            text = item.text.replace(" ", "").strip()
            if "目前店數" in text:
                info_span = item.select_one("span.info")
                if info_span and info_span.text.strip().isdigit():
                    branches_count = int(info_span.text.strip())
            elif "成立時間" in text:
                info_span = item.select_one("span.info")
                if info_span and info_span.text.strip().isdigit():
                    established_time = int(info_span.text.strip())
            elif "產品" in text:
                info_span = item.select_one("span.info")
                product_type = (
                    info_span.text.strip()
                    if info_span
                    else text.replace("產品:", "")
                )

        brands_data.append(
            {
                "brand_name": brand_name,
                "total_stores": branches_count,
                "established_year": established_time,
                "product_type": product_type,
            }
        )

    df_brands = pd.DataFrame(brands_data)

    # 寫入 MySQL (為避免重複寫入，若是全新跑可用 append，如果想更新可以清空或用適當機制)
    try:
        df_brands.to_sql(
            name="brands", con=engine, if_exists="append", index=False
        )
        print("✅ 品牌資料已成功寫入 `brands` 資料表！")
    except Exception as e:
        print(f"⚠️ 寫入品牌資料時發生提示/錯誤：{e}")


# ==========================================
# 步驟 2：門市資料爬蟲與寫入
# ==========================================
def process_stores(engine):
    print("\n🚀 [階段二] 開始讀取品牌 ID 並抓取門市資料...")

    # 從資料庫撈取最新的品牌 Map
    brands_df = pd.read_sql(
        "SELECT brand_id, brand_name FROM brands;", con=engine
    )
    brand_map = dict(zip(brands_df["brand_name"], brands_df["brand_id"]))

    all_stores = []

    # --- 範例：王品牛排門市爬蟲 ---
    if "王品牛排" in brand_map:
        target_id = brand_map["王品牛排"]
        url = "https://www.wangsteak.com.tw/store.php"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36"
            )
        }

        try:
            res = requests.get(url, headers=headers)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")

            card_contents = soup.select("div.card-content")
            for card in card_contents:
                title_el = card.select_one("div.title")
                store_name = title_el.text.strip() if title_el else ""

                phone_el = card.select_one("a.phone")
                phone = phone_el.text.strip() if phone_el else ""

                addr_el = card.select_one("a.address")
                address = addr_el.text.strip() if addr_el else ""

                booking_el = card.select_one(
                    "div.btn-control a[href*='inline'], div.btn-control a"
                )
                booking_url = (
                    booking_el["href"]
                    if booking_el and booking_el.has_attr("href")
                    else None
                )

                city, district = parse_address_info(address)

                if store_name:
                    all_stores.append(
                        {
                            "brand_id": target_id,
                            "store_name": store_name,
                            "full_name": f"王品牛排 {store_name}",
                            "address": address,
                            "city": city,
                            "district": district,
                            "phone": phone,
                            "booking_url": booking_url,
                            "business_hours": "詳見官網",
                            "status": "營業中",
                        }
                    )
            print(f"✅ 王品牛排：成功解析 {len(all_stores)} 筆門市！")
        except Exception as e:
            print(f"❌ 抓取王品牛排門市失敗: {e}")

    # 寫入門市資料到 MySQL
    if all_stores:
        df_stores = pd.DataFrame(all_stores)
        try:
            df_stores.to_sql(
                name="stores", con=engine, if_exists="append", index=False
            )
            print("✅ 門市資料已成功寫入 `stores` 資料表！")
        except Exception as e:
            print(f"❌ 寫入門市資料庫失敗：{e}")


# ==========================================
# 主流程控制
# ==========================================
def main():
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER") or input("DB user: ")
    DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass(
        "DB password: "
    )
    DB_NAME = os.environ.get("DB_NAME", "wowprime")

    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url)

    # 執行階段一：品牌
    #process_brands(engine)

    # 執行階段二：門市
    process_stores(engine)


# if __name__ == "__main__":
#     main()