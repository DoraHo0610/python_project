import base64
import os
import pandas as pd
from dotenv import load_dotenv
import folium
from folium.plugins import MarkerCluster
from sqlalchemy import create_engine
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="品牌地圖 GIS - 王品小幫手", page_icon="📍", layout="wide"
)

# 頁頭與回首頁按鈕
col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("📍 3. 王品集團品牌地圖 GIS 圖示化分析")
with col_home:
    if st.button("🏠 回首頁", key="top_home_4"):
        st.switch_page("Wowprime.py")

st.markdown("---")

load_dotenv("./.env", override=True)


@st.cache_data
def load_data():

    # DB_HOST = os.environ.get("DB_HOST", "localhost")
    # DB_PORT = int(os.environ.get("DB_PORT", 3306))
    # DB_USER = os.environ.get("DB_USER", "root")
    # DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    # DB_NAME = os.environ.get("DB_NAME", "wowprime")

    # engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    # engine = create_engine(engine_url)


    # query = "SELECT s.*, b.brand_name FROM stores s LEFT JOIN brands b ON s.brand_id = b.brand_id WHERE s.status = '營業中';"
    # df = pd.read_sql(query, engine)
    # df = df.dropna(subset=["google_rating", "google_review_count"])
    # df["brand_name"] = df["brand_name"].fillna("未知品牌")
    # return df


    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME = os.environ.get("DB_NAME", "wowprime")

    engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(engine_url)

    query = "SELECT s.*, b.brand_name FROM stores s LEFT JOIN brands b ON s.brand_id = b.brand_id WHERE s.status = '營業中';"
    df = pd.read_sql(query, engine)
    df = df.dropna(subset=["google_rating", "google_review_count"])
    df["brand_name"] = df["brand_name"].fillna("未知品牌")
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"❌ 資料載入失敗: {e}")
    st.stop()


# 💡 圖片轉 Base64 防呆機制
def get_image_base64(img_path):
    if os.path.exists(img_path):
        with open(img_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None


# ----------------------------------------------------
# 篩選下拉選單
# ----------------------------------------------------
filter_col1, filter_col2 = st.columns(2)

brand_list = ["全部品牌"] + sorted(df_raw["brand_name"].unique().tolist())
city_list = ["全部縣市"] + sorted(df_raw["city"].unique().tolist())

with filter_col1:
    selected_brand = st.selectbox("🔍 請選擇品牌", brand_list)

with filter_col2:
    selected_city = st.selectbox("📍 請選擇縣市", city_list)

df_filtered = df_raw.copy()
if selected_brand != "全部品牌":
    df_filtered = df_filtered[df_filtered["brand_name"] == selected_brand]
if selected_city != "全部縣市":
    df_filtered = df_filtered[df_filtered["city"] == selected_city]

st.info(
    f"💡 當前呈現：**[{selected_brand}]** + **[{selected_city}]**，共 **{len(df_filtered)}** 家門市"
)

# ----------------------------------------------------
# 繪製 Folium 地圖
# ----------------------------------------------------
if not df_filtered.empty:
    avg_lat = df_filtered["latitude"].mean()
    avg_lng = df_filtered["longitude"].mean()

    # 建立地圖物件
    m = folium.Map(
        location=[avg_lat, avg_lng], zoom_start=10, tiles="OpenStreetMap"
    )
    marker_cluster = MarkerCluster().add_to(m)

    PICTURE_FOLDER = "picture"

    for _, row in df_filtered.iterrows():
        if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
            booking_html = (
                f"<a href='{row['booking_url']}' target='_blank' style='color: white; background-color: #ff4b4b; padding: 4px 8px; text-decoration: none; border-radius: 4px;'>👉 點我線上訂位</a>"
                if pd.notnull(row["booking_url"])
                and str(row["booking_url"]).startswith("http")
                else "<span style='color: gray;'>無線上訂位</span>"
            )

            popup_content = f"""
            <div style="font-family: Arial, sans-serif; width: 220px; font-size: 14px; line-height: 1.5;">
                <h4 style="margin-top:0; margin-bottom: 8px; color: #333333;"><b>{row['full_name']}</b></h4>
                <b>⭐ Google 評分：</b> {row['google_rating']} 分<br>
                <b>💬 評論次數：</b> {int(row['google_review_count']):,} 則<br>
                <b>💰 平均價位：</b> NT$ {int(row['avg_price'])}<br>
                <b>📍 地址：</b> {row['address']}<br><br>
                {booking_html}
            </div>
            """

            # 讀取圖片或使用預設 Icon
            brand_name = str(row["brand_name"]).strip()
            png_path = os.path.join(PICTURE_FOLDER, f"{brand_name}.png")
            base64_img = get_image_base64(png_path)

            if base64_img:
                marker_icon = folium.CustomIcon(
                    base64_img, icon_size=(35, 35)
                )
            else:
                marker_icon = folium.Icon(
                    color="red", icon="cutlery", prefix="fa"
                )

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{row['full_name']} (⭐ {row['google_rating']}分)",
                icon=marker_icon,
            ).add_to(marker_cluster)

    # 🌟 關鍵修復點 1：改用 Folium 官方渲染器，完全去除破壞排版的 custom_style
    map_html = m.get_root().render()

    # 🌟 關鍵修復點 2：直接使用 components.html 渲染，指定固定高度 750px
    components.html(map_html, height=750, scrolling=True)

else:
    st.warning("⚠️ 查無符合條件的門市，請變更上方下拉選單篩選條件！")

st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_4"):
    st.switch_page("Wowprime.py")