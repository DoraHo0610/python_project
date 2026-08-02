import os
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="聲譽與價格相關性 - 王品小幫手", page_icon="📈", layout="wide"
)

# 頁頭與回首頁按鈕
col_title, col_home = st.columns([5, 1])
with col_title:
    st.title("📈 3. 消費者聲譽與綜合交叉維度分析")
with col_home:
    if st.button("🏠 回首頁", key="top_home_3"):
        st.switch_page("Wowprime.py")

st.markdown("---")


def load_responsive_html_chart(file_path, height=900):
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
            f"❌ 找不到圖表檔案 `{file_path}`！請先執行 `wowprime_analyst.py` 產出 HTML 圖表。"
        )


# ----------------------------------------------------
# 1. 上圖：面向 3 - 評分 vs. 評論數四象限圖 (chart3_reputation_quadrant.html)
# ----------------------------------------------------
st.subheader("3.1 門市聲譽四象限矩陣圖")
load_responsive_html_chart("chart3_reputation_quadrant.html", height=900)

st.markdown("---")

# ----------------------------------------------------
# 2. 下圖：面向 4 - 客單價 vs. Google 評分相關性分析 (chart4_price_vs_rating_overall.html)
# ----------------------------------------------------
st.subheader("3.2 門市客單價與 Google 評分相關性分析 (全集團整體)")
load_responsive_html_chart("chart4_price_vs_rating_overall.html", height=900)

st.markdown("---")
if st.button("🏠 回到首頁", key="bottom_home_3"):
    st.switch_page("Wowprime.py")