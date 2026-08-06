import streamlit as st
import os
from PIL import Image

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine

# 1. 讀取圖片
icon_image = Image.open("picture/wowprime.jpg")

# 2. 網頁標籤
st.set_page_config(
    page_title="王品集團品牌統計分析",
    page_icon="🍽️",  # 👈 網頁標籤維持皇冠
    layout="wide",
)

# ---------------------------------------------------------
# 🎯 標題區域：圖片 + 文字並排
# ---------------------------------------------------------
# 建立兩個欄位，第一個欄位放圖片（寬度給 1），第二個欄位放標題文字（寬度給 15）
col1, col2 = st.columns([1, 15])

with col1:
    # 顯示 Logo 圖片，width 可以自由調整圖片的大小（例如 80 或 100 像素）
    st.image(icon_image, width=100)

with col2:
    # 顯示大標題
    st.title("王品集團 -瘋美食- 品牌統計分析")

#st.markdown("---")


st.markdown("### 💡 歡迎來到本分析平台，這是王品集團吃貨玩家的小幫手！")

# 🎯 將 st.write 改為 st.markdown，並加入 style 調整文字大小
st.markdown(
    '<p style="font-size: 20px; color: #333333; line-height: 1.6;">'
    "本平台整合王品集團全台門市數據、Google 地圖消費評論與 Google地理座標全台門分布以及訂位資訊，提供全方位的商業決策支援與消費者互動體驗。"
    "</p>",
    unsafe_allow_html=True,
)


# 載入環境變數
load_dotenv("./.env", override=True)


# ----------------------------------------------------
# 1. 資料庫連線與資料載入
# ----------------------------------------------------
@st.cache_data
def load_brands_data():
    """從 MySQL 資料庫撈取前 20 筆品牌資料（排除購物網與集團）"""
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "wowprime")

    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url)

    # SQL 查詢：排除非實體門市品牌，撈取前 20 筆
    query = """
    SELECT brand_name, total_stores, established_year, product_type 
    FROM brands 
    WHERE brand_name NOT IN ('王品瘋美食購物網', '王品集團') 
    ORDER BY brand_id ASC 
    LIMIT 20;
    """
    df_brands = pd.read_sql(query, engine)
    return df_brands


try:
    df_brands = load_brands_data()
except Exception as e:
    st.error(f"❌ 資料庫連線或資料載入失敗: {e}")
    st.stop()


# ----------------------------------------------------
# 品牌一覽卡片區塊 (每列 5 家品牌)
# ----------------------------------------------------
#st.title("🍽️ 王品集團旗下主要品牌一覽")
st.markdown("### 🍽️ 王品集團旗下主要品牌一覽")

picture_dir = "picture"

# 每行呈現 5 個品牌卡片
N_COLS = 10

for row_idx in range(0, len(df_brands), N_COLS):
    cols = st.columns(N_COLS)
    # 取出這一行的品牌資料列
    sub_df = df_brands.iloc[row_idx : row_idx + N_COLS]

    for col_i, (_, brand_row) in zip(cols, sub_df.iterrows()):
        brand_name = brand_row["brand_name"]
        total_stores = int(brand_row["total_stores"])
        est_year = (
            int(brand_row["established_year"])
            if pd.notnull(brand_row["established_year"])
            else "未知"
        )
        product_type = brand_row["product_type"]

        with col_i:
            # 建立造型卡片外框
            with st.container(border=True):
                # 1. 展示品牌 Logo 圖片
                img_path = os.path.join(picture_dir, f"{brand_name}.png")
                if os.path.exists(img_path):
                    # 💡 這裡已修改為 use_container_width=True
                    st.image(img_path, use_container_width=True)
                else:
                    st.markdown(
                        f"<h4 style='text-align: center; color: #ff4b4b;'>🍽️ {brand_name}</h4>",
                        unsafe_allow_html=True,
                    )

                # # 2. 品牌詳細資訊
                # st.markdown(f"**{brand_name}**")
                # st.caption(f"🍳**料理形式**：{product_type}")  
                # st.caption(f"🏪 **全台店數**：{total_stores} 家門市")
                # st.caption(f"📅 **成立年份**：{est_year} 年")


                # 2. 品牌詳細資訊 (透過 HTML/CSS 自訂字體大小與邊距)
                st.markdown(
                    f"""
                    <div style="color: #333333; line-height: 1.3;">
                        <p style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">{brand_name}</p>
                        <p style="font-size: 15px; margin-bottom: 6px;">
                            🍳 <b>料理形式</b>：<br>
                            <span style="margin-left: 22px; display: inline-block;">{product_type}</span>
                        </p>
                        <p style="font-size: 15px; margin-bottom: 6px;">
                            🏪 <b>全台店數</b>：<br>
                            <span style="margin-left: 22px; display: inline-block;">{total_stores} 家門市</span>
                        </p>
                        <p style="font-size: 15px; margin-bottom: 0px;">
                            📅 <b>成立年份</b>：<br>
                            <span style="margin-left: 22px; display: inline-block;">{est_year} 年</span>
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )



st.markdown("---")
st.markdown("### ● 請選擇您想體驗的功能服務：")

# ---------------------------------------------------------
# 第一列：放 1, 2 (切成 2 欄)
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info("#### 📊 1. 各品牌門市規模分析")
    st.write("王品旗下各品牌在全台灣的門市規模與分布狀況。")
    if st.button("👉 前往頁面", key="nav_1", use_container_width=True):
        st.switch_page("pages/1_page1.py")

with col2:
    st.info("#### 📊 2. 各品牌Google評分分析")
    st.write("Google評分與品牌分類之相關性分析。")
    if st.button("👉 前往頁面", key="nav_2", use_container_width=True):
        st.switch_page("pages/2_page2.py")



# st.markdown("---")
# st.markdown("### ● 請選擇您想體驗的功能服務：")
# ---------------------------------------------------------
# 第二列：放 3, 4 
# ---------------------------------------------------------
#col3, col4 = st.columns(2)

with col3:
    st.success("#### 📍 3. 品牌地圖 GIS")
    st.write("互動式 GIS 地圖，支援按品牌與縣市即時篩選。")
    if st.button("👉 前往頁面", key="nav_3", use_container_width=True):
        st.switch_page("pages/3_page3.py")

with col4:
    st.warning("#### 🎲 4. 美食隨機轉盤")
    st.write("不知道吃什麼？透過轉盤小幫手幫您隨機抽選！")
    if st.button("👉 前往頁面", key="nav_4", use_container_width=True):
        st.switch_page("pages/4_page4.py")

st.markdown("---")
st.caption("Powered by Streamlit | 數據源：王品集團官網 & Google Maps API")