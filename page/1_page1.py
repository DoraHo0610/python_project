import getpass
import os
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import streamlit as st

st.set_page_config(page_title="品牌規模與評分 - 王品小幫手", page_icon="📊", layout="wide")

col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("📊 1. 品牌規模與評分分佈分析")
with col_home:
    if st.button("🏠 回首頁", key="top_home_1"):
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

# ----------------------------------------------------
# 上圖：1.1 品牌門市數量排行榜
# ----------------------------------------------------
st.subheader("1.1 王品集團各品牌門市規模排行榜")
brand_counts = df["brand_name"].value_counts().reset_index()
brand_counts.columns = ["brand_name", "store_count"]

fig1 = px.bar(
    brand_counts,
    x="brand_name",
    y="store_count",
    title="各品牌門市數量排行榜",
    labels={"brand_name": "品牌名稱", "store_count": "門市數量"},
    color="store_count",
    color_continuous_scale="Purpor",
    text="store_count",
)
fig1.update_layout(
    xaxis={"categoryorder": "total descending", "tickangle": -45},
    yaxis_title="門市數量",
    xaxis_title="品牌名稱",
    template="plotly_white",
    height=450,
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# 下圖：1.2 各品牌評分區間分佈 (Box Plot)
# ----------------------------------------------------
st.subheader("1.2 王品集團各品牌評分區間分佈 (Box Plot)")
fig2 = px.box(
    df,
    x="brand_name",
    y="google_rating",
    color="brand_name",
    title="各品牌 Google 評分分佈情況",
    labels={"google_rating": "Google 評分", "brand_name": "品牌名稱"},
)
fig2.update_layout(
    showlegend=False, xaxis_tickangle=-45, template="plotly_white", height=450
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_1"):
    st.switch_page("app.py")