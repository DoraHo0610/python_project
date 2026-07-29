import getpass
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import streamlit as st

st.set_page_config(page_title="縣市展店佈局 - 王品小幫手", page_icon="🗺️", layout="wide")

col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("🗺️ 2. 地理區域與展店策略分析")
with col_home:
    if st.button("🏠 回首頁", key="top_home_2"):
        st.switch_page("app.py")

st.markdown("---")

load_dotenv("./.env", override=True)


@st.cache_data
def load_data():
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
    if "google_place_id" in df.columns:
        df = df.drop(columns=["google_place_id"])
    df["brand_name"] = df["brand_name"].fillna("未知品牌")
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"❌ 資料載入失敗: {e}")
    st.stop()

col_left, col_right = st.columns([1, 1.3])

# ----------------------------------------------------
# 左圖：2.1 各縣市門市數量分佈
# ----------------------------------------------------
with col_left:
    st.subheader("2.1 各縣市門市數量分佈")
    city_counts = df["city"].value_counts().reset_index()
    city_counts.columns = ["city", "store_count"]

    fig1 = px.pie(
        city_counts,
        values="store_count",
        names="city",
        title="王品集團全台門市縣市分佈比例",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig1.update_layout(height=500)
    st.plotly_chart(fig1, use_container_width=True)

# ----------------------------------------------------
# 右圖：2.2 縣市 x 品牌門市數量熱力圖 (Heatmap)
# ----------------------------------------------------
with col_right:
    st.subheader("2.2 各縣市門市品牌佈局熱力矩陣")
    city_brand_pivot = pd.crosstab(df["city"], df["brand_name"])

    fig2 = px.imshow(
        city_brand_pivot,
        labels=dict(x="品牌名稱", y="縣市", color="門市數"),
        x=city_brand_pivot.columns,
        y=city_brand_pivot.index,
        title="縣市 x 品牌熱力矩陣",
        color_continuous_scale="YlOrRd",
        text_auto=True,
    )
    fig2.update_layout(template="plotly_white", height=500)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_2"):
    st.switch_page("app.py")