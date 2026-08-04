import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="品牌規模 - 王品小幫手", page_icon="📊", layout="wide"
)

# 頁頭與回首頁按鈕
col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("📊 1. 品牌門市規模分析")
with col_home:
    if st.button("🏠 回首頁", key="top_home_1"):
        st.switch_page("Wowprime.py")

st.markdown("---")


def load_responsive_html_chart(file_path, height=750):
    """讀取 HTML 圖表並注入 CSS/JS，

    強制將 Plotly 的繪圖畫布 (SVG / Canvas) 放大並填滿容器。
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # 注入 CSS 樣式與 JS 重繪事件：覆蓋內建的固定寬高限制，強迫 100% 展開
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
            responsive_html = html_content.replace(
                "</head>", f"{custom_style}</head>"
            )
        else:
            responsive_html = custom_style + html_content

        components.html(responsive_html, height=height, scrolling=False)
    else:
        st.error(
            f"❌ 找不到圖表檔案 `{file_path}`！請先執行分析腳本產出 HTML 圖表。"
        )


# ----------------------------------------------------
# 1.1 品牌門市數量排行榜
# ----------------------------------------------------
st.subheader("圖1 - 分析各品牌的門市規模大小，了解哪些是集團主力展店品牌:")
load_responsive_html_chart("chart1-1_brand_store_counts.html", height=800)

st.markdown("---")

# ----------------------------------------------------
# 1.2 各品牌門市數量與成立年份相關性分析
# ----------------------------------------------------
st.subheader("圖2 - 透過散佈圖與趨勢線，探索「品牌成立越久，門市數量是否越多」:")
load_responsive_html_chart("chart1-2_store_count_vs_year.html", height=800)

st.markdown("---")

# ----------------------------------------------------
# 1.3 全台門市縣市分佈比例圓餅圖
# ----------------------------------------------------
st.subheader("圖3 - 分析集團門市在全台各縣市的比例，主要消費市場集中在六都:")
load_responsive_html_chart("chart1-3_city_distribution_piechart.html", height=800)

st.markdown("---")

# ----------------------------------------------------
# 1.4 各縣市門市品牌佈局熱力矩陣圖
# ----------------------------------------------------
st.subheader("圖4 - 分析不同縣市與各品牌間的交叉展店密度:")
load_responsive_html_chart("chart1-4_city_brand_heatmap.html", height=800)

st.markdown("---")


if st.button("🏠 回到首頁", key="bottom_home_1"):
    st.switch_page("Wowprime.py")