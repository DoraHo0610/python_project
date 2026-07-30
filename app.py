import streamlit as st
import os

st.set_page_config(
    page_title="王品集團品牌統計分析小幫手",
    page_icon="👑",
    layout="wide",
)

st.title("👑 王品集團旗下品牌統計分析小幫手")
st.markdown("---")

# st.image(
#     "https://pitchbook.com/profiles/company/164521-54",
#     use_container_width=True,
#     caption="王品集團 Wowprime - 創造顧客體驗的餐飲領導品牌",
# )

# st.image(
#     "wowprime1.jpg",
#     width=100,  # 指定寬度為 400 像素
#     caption="王品集團 Wowprime - 創造顧客體驗的餐飲領導品牌",
# )




st.markdown("### 💡 歡迎使用本分析平台！")
st.write(
    "本平台整合王品集團全台門市數據、Google 地圖消費評論與地理座標，提供全方位的商業決策支援與消費者互動體驗。"
)

st.markdown("---")
st.markdown("### 🚀 請選擇您想體驗的功能服務：")

col1, col2, col3, col4, col5 = st.columns(5)

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

with col4:
    st.success("#### 📍 4. 品牌地圖 GIS")
    st.write("互動式 GIS 地圖，支援按品牌與縣市即時篩選。")
    if st.button("👉 前往頁面", key="nav_4", use_container_width=True):
        st.switch_page("pages/4_page4.py")

with col5:
    st.warning("#### 🎲 5. 選擇障礙小幫手")
    st.write("不知道吃什麼？透過動態轉盤幫您隨機抽選！")
    if st.button("👉 前往頁面", key="nav_5", use_container_width=True):
        st.switch_page("pages/5_page5.py")

st.markdown("---")
st.caption("Powered by Streamlit | 數據源：王品集團官網 & Google Maps API")