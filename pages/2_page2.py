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
        st.switch_page("Wowprime.py")

st.markdown("---")


def load_responsive_html_chart(file_path, height=1000):
    """
    讀取 HTML 圖表並注入 CSS/JS，
    強制將 Plotly 的繪圖畫布 (SVG / Canvas) 放大並填滿容器。
    """
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
            f"❌ 找不到圖表檔案 `{file_path}`！請先執行 `wowprime_analyst.py` 產出 HTML 圖表。"
        )


# ----------------------------------------------------
# 1. 上圖：2.1 全台門市縣市分佈比例 
# ----------------------------------------------------
st.subheader("2.1 王品集團各門市Google評分四象限圖")
load_responsive_html_chart("chart2-1_rating_scatter_plot.html", height=1000)

st.markdown("---")

# ----------------------------------------------------
# 2. 下圖：2.2 各縣市門市品牌佈局熱力矩陣 
# ----------------------------------------------------
st.subheader("2.2 王品集團各品牌Google評分盒狀圖")
load_responsive_html_chart("chart2-2_brand_rating_boxplot.html", height=1000)

# ----------------------------------------------------
# 3. 下圖：2.3 品牌加權評分與平均客單價相關性分析
# ----------------------------------------------------
st.subheader("2.3 王品集團各品牌'Google加權平均分數'與'平均客單價'相關性分析")
load_responsive_html_chart("chart2-3_price_vs_rating_overall.html", height=1000)


# ----------------------------------------------------
# 4. 下圖：2.4 品牌加權評分與成立年份相關性分析
# ----------------------------------------------------
st.subheader("2.4 王品集團各品牌'Google加權平均分數'與'平均客單價'相關性分析")
load_responsive_html_chart("chart2-4_year_vs_rating.html", height=1000)


# ----------------------------------------------------
# 4. 下圖：2.5 王品集團各餐廳類型之 Google 加權平均分佈
# ----------------------------------------------------
st.subheader("2.5 王品集團各餐廳類型之 Google 加權平均分佈")
load_responsive_html_chart("chart2-5_type_rating_boxplot.html", height=1000)




st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_2"):
    st.switch_page("Wowprime.py")