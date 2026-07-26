import pandas as pd
import os
import getpass
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv("./.env", override=True)


# ==========================================
# 1. 爬蟲階段：抓取王品品牌資料
# ==========================================
url = "https://www.wowprime.com/zh-tw/investors-sub-menu/about-wowprime/brand-introduction/taiwan"  # 請替換為實際的各品牌店數網址

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers)
response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "html.parser")

brands_data = []
cards = soup.select("div.brands-list div.wrap")

for card in cards:
    # 抓取品牌名稱
    title_tag = card.select_one("div.title")
    brand_name = title_tag.text.strip() if title_tag else "未知品牌"

    # 解析條目 (店數、成立時間、產品)
    items = card.select("div.info-wrap div.item")

    branches_count = None
    established_time = None
    product_type = None

    for item in items:
        text = item.text.replace(" ", "").strip()

        if "目前店數" in text:
            info_span = item.select_one("span.info")
            # 轉為數字型態 (防呆處理)
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

# 轉換為 DataFrame
df = pd.DataFrame(brands_data)
print("=== 成功抓取資料 ===")
print(df)



# ==========================================
# 2. 資料庫匯入階段：寫入 MySQL
# ==========================================
# 讀取帳密(優先從環境變數存取，不存在才互動式要求）
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER") or input("DB user: ")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass("DB password: ")
DB_NAME = os.environ.get("DB_NAME", "wowprime")

# 建立 MySQL 資料庫引擎
engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(engine_url)

# 將 DataFrame 寫入 MySQL 的 'brands' 資料表
# if_exists='append': 如果資料表已存在，追加寫入 (若是初次建立可設為 'replace')
# index=False: 不把 Pandas 的索引欄位 (0, 1, 2...) 寫進資料庫
try:
    df.to_sql(
        name="brands", con=engine, if_exists="append", index=False
    )
    print("\n✅ 資料已成功匯入 MySQL 資料庫中的 `brands` 資料表！")
except Exception as e:
    print(f"\n❌ 匯入資料庫失敗，錯誤訊息：{e}")