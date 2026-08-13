import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="各品牌Google評分分析", page_icon="🗺️", layout="wide"
)

# 頁頭與回首頁按鈕
col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("🗺️ 2. 王品集團各品牌Google評分分析")
with col_home:
    if st.button("🏠 回首頁", key="top_home_2"):
        st.switch_page("wowprime.py")

st.markdown("---")


def load_responsive_html_chart(file_name, height=800):
    file_path = os.path.join("html", file_name)
    
    #讀取 HTML 圖表並注入 CSS/JS，強制將 Plotly 的繪圖畫布 (SVG / Canvas) 放大並填滿容器。
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 注入 CSS 樣式：覆蓋內建的固定寬高限制，強迫 100% 展開
        custom_style = """
        <style>
            html, body {
                width: 100% !important;
                height: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }
            .plotly-graph-div {
                width: 100% !important;
                height: 100vh !important;
            }
            .svg-container {
                width: 100% !important;
                height: 100% !important;
                margin: 0 auto !important;
            }
            .main-svg {
                width: 100% !important;
            }
        </style>
        <script>
            // 頁面載入完成後，強制觸發 Plotly 自適應重繪
            window.addEventListener('load', function() {
                setTimeout(function() {
                    window.dispatchEvent(new Event('resize'));
                }, 200);
            });
        </script>
        """

        # 將自訂 CSS/JS 插入至 HTML 的 <head> 中
        if "</head>" in html_content:
            responsive_html = html_content.replace("</head>", f"{custom_style}</head>")
        else:
            responsive_html = custom_style + html_content

        components.html(responsive_html, height=height, scrolling=False)
    else:
        st.error(
            f"❌ 找不到圖表檔案 `{file_path}`！請先執行分析腳本產出 HTML 圖表。"
        )


# ----------------------------------------------------
# 2.1 王品集團各門市Google評分四象限圖 
# ----------------------------------------------------
st.subheader("圖1 - 以『評分與評論數中位數』切分四大象限，快速辨識出高滿意度且高人氣的明星旗艦門市:")
load_responsive_html_chart("chart2-1_rating_scatter_plot.html", height=800)

st.markdown("---")

# ----------------------------------------------------
# 2.2 王品集團各品牌Google評分盒狀圖 
# ----------------------------------------------------
st.subheader("圖2 - 利用盒狀圖 剖析各品牌旗下門市評分的集中趨勢與離散程度，評估品牌整體服務品質控管的穩定度:")
load_responsive_html_chart("chart2-2_brand_rating_boxplot.html", height=800)

st.markdown("---")

# ----------------------------------------------------
# 2.3 品牌加權評分與平均客單價相關性分析
# ----------------------------------------------------
st.subheader("圖3 - 結合門市評論數權重與平均客單價，透過迴歸分析評估『消費金額越高，顧客給予的滿意度評分是否越高』:")
load_responsive_html_chart("chart2-3_price_vs_rating_overall.html", height=800)

st.markdown("---")

# ----------------------------------------------------
# 2.4 品牌加權評分與成立年份相關性分析
# ----------------------------------------------------
# st.subheader("圖4 - 探索品牌成立時間長短對顧客評分的影響，觀察老字號經典品牌與新創潮牌在聲譽維護上的表現差異:")
# load_responsive_html_chart("chart2-4_year_vs_rating.html", height=800)
# #st.caption("探索品牌成立時間長短對顧客評分的影響，觀察老字號經典品牌與新創潮牌在聲譽維護上的表現差異。")

# st.markdown("---")

# ----------------------------------------------------
# 2.4 王品集團各餐廳類型之 Google 加權平均分佈
# ----------------------------------------------------
st.subheader("圖4 - 按餐飲品類（如燒肉、鍋物、鐵板燒等）進行評分分佈比較，解析不同餐飲業態在消費者心目中的滿意度:")
load_responsive_html_chart("chart2-5_type_rating_boxplot.html", height=800)

st.markdown("---")

if st.button("🏠 回到首頁", key="bottom_home_2"):
    st.switch_page("wowprime.py")

# ---------------------------------------------------------
# 頁尾：技術標籤、開發者權益與免責聲明
# ---------------------------------------------------------
st.markdown("---")

# 1. 技術框架與數據源標示
st.caption(
    "Powered by Streamlit | 數據來源：王品集團官網 & Google Maps 公開數據"
)

# 2. 開發者資訊與原創保護聲明
st.caption(
    "**專案開發者：何莉維 | 開發時間：2026年8月 **"
    "**聲明 (Disclaimer & Copyright)**：\n"
    "1. 原創聲明與著作權保護：本專案程式碼、UI 佈局與數據分析架構由開發者獨立完成，僅作為個人作品集展示（Academic"
    " Portfolio）。未經原作者授權，禁止擅自複製、抄襲重製或作為他人課程作業/報告提交。\n"
    "2. 數據與商標權屬：本專案無任何商業營利用途。專案中引用之品牌名稱、LOGO 商標與門市公開數據，其智慧財產權分別歸王品集團與"
    " Google 所有。"
)
