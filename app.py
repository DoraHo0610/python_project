import streamlit as st
import os
from PIL import Image

import streamlit as st
from PIL import Image

# 1. 讀取圖片
icon_image = Image.open("wowprime.jpg")

# 2. 網頁標籤
st.set_page_config(
    page_title="王品集團品牌統計分析",
    page_icon="👑",  # 👈 網頁標籤維持皇冠
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
    st.title("王品集團品牌統計分析")

#st.markdown("---")


st.markdown("### 💡 歡迎來到本分析平台，這是王品集團吃貨玩家的小幫手！")
st.write(
    "本平台整合王品集團全台門市數據、Google 地圖消費評論與 Google地理座標全台門分布以及訂位資訊，提供全方位的商業決策支援與消費者互動體驗。"
)

st.markdown("---")
st.markdown("### ● 以下三個王品集團旗下品牌分析面向 供您參考：")

# ---------------------------------------------------------
# 第一列：放 1, 2, 3 (切成 3 欄)
# ---------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.info("#### 📊 1. 品牌規模與評分")
    st.write("各品牌門市規模排行榜與 Google 評分箱型圖。")
    if st.button("👉 前往頁面", key="nav_1", use_container_width=True):
        st.switch_page("pages/1_page1.py")

with col2:
    st.info("#### 🗺️ 2. 縣市展店佈局")
    st.write("全台門市縣市比例與各縣市品牌佈局熱力矩陣。")
    if st.button("👉 前往頁面", key="nav_2", use_container_width=True):
        st.switch_page("pages/2_page2.py")

with col3:
    st.info("#### 📈 3. 聲譽與價格相關性")
    st.write("門市聲譽四象限矩陣與客單價 vs 評分相關性分析。")
    if st.button("👉 前往頁面", key="nav_3", use_container_width=True):
        st.switch_page("pages/3_page3.py")



st.markdown("---")
st.markdown("### ● 請選擇您想體驗的功能服務：")
# ---------------------------------------------------------
# 第二列：放 4, 5 (切成 3 欄，第 3 欄留空，讓卡片對齊上方)
# ---------------------------------------------------------
col4, col5 = st.columns(2)

with col4:
    st.success("#### 📍 4. 品牌地圖 GIS")
    st.write("互動式 GIS 地圖，支援按品牌與縣市即時篩選。")
    if st.button("👉 前往頁面", key="nav_4", use_container_width=True):
        st.switch_page("pages/4_page4.py")

with col5:
    st.warning("#### 🎲 5. 吃貨選擇小幫手")
    st.write("不知道吃什麼？透過動態轉盤幫您隨機抽選！")
    if st.button("👉 前往頁面", key="nav_5", use_container_width=True):
        st.switch_page("pages/5_page5.py")

st.markdown("---")
st.caption("Powered by Streamlit | 數據源：王品集團官網 & Google Maps API")