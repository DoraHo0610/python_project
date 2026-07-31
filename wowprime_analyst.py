import getpass
import os
from dotenv import load_dotenv
import folium
from folium.plugins import MarkerCluster
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

# ====================================================
# 1. 載入 .env 設定並連線資料庫讀取資料
# ====================================================
load_dotenv("./.env", override=True)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER") or input("DB user: ")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass("DB password: ")
DB_NAME = os.environ.get("DB_NAME", "wowprime")

engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(engine_url)

print("🔍 正在讀取資料庫門市與品牌聯結資料...")
query = """
SELECT 
    s.*, 
    b.brand_name 
FROM stores s
LEFT JOIN brands b ON s.brand_id = b.brand_id
WHERE s.status = '營業中';
"""
df = pd.read_sql(query, engine)

# ====================================================
# 1.1 資料預處理防錯 (依需求修改)
# ====================================================
# 1. 若 google_rating 或是 google_review_count 有 null 值，移除該列資料
df = df.dropna(subset=["google_rating", "google_review_count"])

# 2. 刪除 google_place_id 欄位 (若存在的話)
if "google_place_id" in df.columns:
    df = df.drop(columns=["google_place_id"])

# 其他欄位基礎預處理
df["avg_price"] = df["avg_price"].fillna(0)
df["brand_name"] = df["brand_name"].fillna("未知品牌")

print(f"✅ 成功載入並清理完成！共獲取 {len(df)} 筆有效分析資料！\n")


# ====================================================
# 面向 1：品牌與市場佈局分析 (Brand & Market Distribution)
# ====================================================
def analyze_brand_market(df):
    print("📊 執行 [面向 1]：品牌門市規模與評分分佈分析...")

    # 1.1 品牌門市數量排行榜 (修改: X 軸為品牌名稱, Y 軸為門市數量)
    brand_counts = df["brand_name"].value_counts().reset_index()
    brand_counts.columns = ["brand_name", "store_count"]

    fig1 = px.bar(
        brand_counts,
        x="brand_name",
        y="store_count",
        title="王品集團各品牌門市規模排行榜",
        labels={"brand_name": "品牌名稱", "store_count": "門市數量"},
        color="store_count",
        color_continuous_scale="Purpor",
        text="store_count",
    )

    # 🌟 修正重點：將 textfont 抽出來使用 update_traces 設定
    fig1.update_traces(textfont=dict(size=14))

    fig1.update_layout(
        template="plotly_white",
        title=dict(font=dict(size=22)),
        xaxis=dict(
            categoryorder="total descending",
            tickangle=-45,
            title=dict(text="品牌名稱", font=dict(size=18)),  # X 軸軸標題
            tickfont=dict(size=16),  # X 軸刻度文字 (各品牌名)
        ),
        yaxis=dict(
            title=dict(text="門市數量", font=dict(size=18)),  # Y 軸軸標題
            tickfont=dict(size=15),  # Y 軸刻度文字 (數字 0, 10, 20...)
        ),
        # 底部留白微調 (防止 X 軸斜放的品牌名稱被切掉)
        margin=dict(b=120),
    )

    fig1.write_html("chart1_brand_store_counts.html")

    # 1.2 各品牌評分區間分佈 (Box Plot)
    fig2 = px.box(
        df,
        x="brand_name",
        y="google_rating",
        color="brand_name",
        title="王品集團各品牌評分區間分佈 (Box Plot)",
        labels={"google_rating": "Google 評分", "brand_name": "品牌名稱"},
    )

    fig2.update_layout(
        showlegend=False,
        template="plotly_white",
        # 調整大標題字型大小
        title=dict(font=dict(size=22)),
        # X 軸文字設定
        xaxis=dict(
            title=dict(text="品牌名稱", font=dict(size=18)),  # X 軸軸標題 (品牌名稱)
            tickfont=dict(size=16),  # X 軸刻度文字 (各品牌名)
            tickangle=-45,
        ),
        # Y 軸文字設定
        yaxis=dict(
            title=dict(text="Google 評分", font=dict(size=18)),  # Y 軸軸標題 (Google 評分)
            tickfont=dict(size=14),  # Y 軸刻度文字 (4, 4.2, 4.4...)
        ),
        # 邊界留白微調（避免字體變大後下方品牌名稱撞到邊界）
        margin=dict(b=130),
    )

    fig2.write_html("chart1_brand_rating_boxplot.html")


# ====================================================
# 面向 2：地理區域與展店策略分析 (Geographic Analysis)
# ====================================================
def analyze_geographic(df):
    print("📊 執行 [面向 2]：縣市門市密度與區域消費力分析...")

    # 2.1 各縣市門市數量分佈
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
    fig1.update_layout(
        template="plotly_white",
        title=dict(font=dict(size=24)),
        legend=dict(font=dict(size=16)),
    )

    # 將圓餅圖內部的百分比數字也放大到 15px
    fig1.update_traces(insidetextfont=dict(size=15))

    fig1.write_html("chart2_city_distribution.html")

    # 2.2 縣市 x 品牌門市數量熱力圖 (Heatmap)
    city_brand_pivot = pd.crosstab(df["city"], df["brand_name"])

    fig2 = px.imshow(
        city_brand_pivot,
        labels=dict(x="品牌名稱", y="縣市", color="門市數"),
        x=city_brand_pivot.columns,
        y=city_brand_pivot.index,
        title="各縣市門市品牌佈局熱力矩陣",
        color_continuous_scale="YlOrRd",
        text_auto=True,
    )

    fig2.update_layout(
        template="plotly_white",
        title=dict(font=dict(size=22)),
        xaxis=dict(
            title=dict(text="品牌名稱", font=dict(size=18)),  # X 軸軸標題
            tickfont=dict(size=13),  # X 軸各品牌名稱
            tickangle=-45,
        ),
        # Y 軸標題與刻度文字 (縣市) 放大
        yaxis=dict(
            title=dict(text="縣市", font=dict(size=18)),  # Y 軸軸標題
            tickfont=dict(size=14),  # Y 軸各縣市名稱
        ),
        # 右側顏色尺規 (Colorbar) 文字放大
        coloraxis_colorbar=dict(
            title=dict(text="門市數", font=dict(size=16)),
            tickfont=dict(size=14),
        ),
        # 底部留白微調 (防止斜放的品牌名稱被切割)
        margin=dict(b=120),
    )

    # 格子內部的數字標籤放大 (13px)
    fig2.update_traces(textfont=dict(size=13))

    fig2.write_html("chart2_city_brand_heatmap.html")


# ====================================================
# 面向 3：消費者聲譽與體驗分析 (Reputation & Feedback)
# ====================================================
def analyze_reputation(df):
    print("📊 執行 [面向 3]：評分 vs. 評論數四象限矩陣分析...")

    median_reviews = df["google_review_count"].median()
    median_rating = df["google_rating"].median()

    # 3.1 評分 (X軸) vs. 評論數 (Y軸) 四象限圖
    fig = px.scatter(
        df,
        x="google_rating",  # X 軸：Google 評分
        y="google_review_count",  # Y 軸：Google 評論總數
        color="brand_name",
        hover_name="full_name",
        hover_data=["city", "avg_price"],
        title=f"門市聲譽四象限圖 (評分中位數: {median_rating}, 評論數中位數: {int(median_reviews)})",
        labels={
            "google_rating": "Google 評分 (1-5)",
            "google_review_count": "Google 評論總數",
            "brand_name": "品牌名稱",
        },
    )

    # 繪製四象限輔助線 (注意：vline 用 x=，hline 用 y=)
    fig.add_vline(
        x=median_rating,
        line_dash="dash",
        line_color="gray",
        annotation_text="評分中位數",
        annotation_font=dict(size=15, color="gray"),
    )
    fig.add_hline(
        y=median_reviews,
        line_dash="dash",
        line_color="gray",
        annotation_text="評論數中位數",
        annotation_font=dict(size=15, color="gray"),
    )

    fig.update_layout(
        template="plotly_white",
        title=dict(font=dict(size=22)),
        xaxis=dict(
            title=dict(text="Google 評分 (1-5)", font=dict(size=18)),  # X 軸軸標題
            tickfont=dict(size=14),  # X 軸刻度數字
        ),
        yaxis=dict(
            title=dict(text="Google 評論總數", font=dict(size=18)),  # Y 軸軸標題
            tickfont=dict(size=14),  # Y 軸刻度數字
        ),
        # 右側品牌圖例 (Legend) 文字放大
        legend=dict(
            title=dict(text="品牌名稱", font=dict(size=16)),
            font=dict(size=14),
        ),
    )

    fig.write_html("chart3_reputation_quadrant.html")


# ====================================================
# 面向 4：綜合交叉維度分析 (Cross-dimensional Insights)
# ====================================================
def analyze_cross_dimensions(df):
    print("📊 執行 [面向 4]：客單價 vs. Google 評分相關性分析...")

    # 防呆機制 1：過濾客單價與評分大於 0 的有效門市資料
    valid_price_df = df[(df["avg_price"] > 0) & (df["google_rating"] > 0)].copy()

    if valid_price_df.empty:
        print("⚠️ 警告：沒有找到有效的客單價與評分資料，跳過面向 4 分析。")
        return

    # 防呆機制 2：若資料中缺少總評論數欄位，預設給予固定點大小
    size_col = "total_reviews" if "total_reviews" in valid_price_df.columns else None

    # ---------------------------------------------------------
    # 🎯 (單一總趨勢線 + 評論數權重)
    # ---------------------------------------------------------
    fig_overall = px.scatter(
        valid_price_df,
        x="avg_price",
        y="google_rating",
        color="brand_name",
        size=size_col,  # 點的大小反映評論數權重 (若無欄位則自動為均等大小)
        trendline="ols",
        trendline_scope="overall",  # 跨品牌全體共用一條總趨勢線
        title="<b>門市客單價與 Google 評分相關性分析 (全集團整體)</b>",
        labels={
            "avg_price": "平均客單價 (NTD)",
            "google_rating": "Google 評分",
            "brand_name": "品牌名稱",
            "total_reviews": "總評論數",
        },
        hover_name="full_name",
        hover_data={
            "avg_price": ":$.0f",
            "google_rating": ":.1f",
            "brand_name": True,
        },
        template="plotly_white",
        height=650,
    )

    # 將標題與座標軸文字放大
    fig_overall.update_layout(
        # 1. 大標題文字放大 (22px)
        title=dict(font=dict(size=22)),
        # 2. X 軸標題與刻度數字放大
        xaxis=dict(
            title=dict(
                text="平均客單價 (NTD)", font=dict(size=18)
            ),  # X 軸軸標題
            tickfont=dict(size=14),  # X 軸刻度數字 (0, 500, 1000...)
        ),
        # 3. Y 軸標題與刻度數字放大
        yaxis=dict(
            title=dict(text="Google 評分", font=dict(size=18)),  # Y 軸軸標題
            tickfont=dict(size=14),  # Y 軸刻度數字 (3.6, 3.8, 4.0...)
            range=[3.5, 5.0],  # 設定 Y 軸範圍
        ),
        # 4. 右側 Legend (品牌名稱圖例) 文字放大
        legend=dict(
            title=dict(text="品牌名稱", font=dict(size=16)),  # Legend 標題
            font=dict(size=14),  # 各品牌名稱項目文字
        ),
    )

    # 匯出方案 A 網頁
    html_a_path = "chart4_price_vs_rating_overall.html"
    fig_overall.write_html(html_a_path)
    print(f"  └─ ✅ 全集團整體分析 已匯出：{html_a_path}")

    return fig_overall


# ====================================================
# 面向 5：空間地理與聚落分析 (Geospatial GIS Map)
# ====================================================
def build_gis_map(df):
    print("🗺️ 執行 [面向 5]：建置 GIS 互動式地圖 (Folium)...")

    # 篩選有效經緯度
    valid_geo_df = df[
        (df["latitude"].notnull()) & (df["longitude"].notnull())
    ]

    # 以台灣中心點 (台中) 初始化地圖
    m = folium.Map(location=[23.973875, 120.982025], zoom_start=8)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in valid_geo_df.iterrows():
        rating = row["google_rating"]

        # 顏色策略：評分 >= 4.7 綠色、4.4-4.6 藍色、< 4.4 紅色
        if rating >= 4.7:
            color = "green"
        elif rating >= 4.4:
            color = "blue"
        else:
            color = "red"

        # 地標 Popup HTML 資訊卡
        booking_link = (
            f"<a href='{row['booking_url']}' target='_blank'>👉 點我線上訂位</a>"
            if pd.notnull(row["booking_url"])
            else "無提供線上訂位"
        )
        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4><b>{row['full_name']}</b></h4>
            <b>⭐ Google 評分：</b> {row['google_rating']} ({int(row['google_review_count'])}則)<br>
            <b>💰 平均客單價：</b> NT$ {int(row['avg_price'])}<br>
            <b>📍 地址：</b> {row['address']}<br>
            <b>🔗 預約：</b> {booking_link}
        </div>
        """

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{row['full_name']} (⭐{row['google_rating']})",
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
        ).add_to(marker_cluster)

    m.save("gis_map_stores.html")
    print("  ✓ 已成功匯出 GIS 地圖至 `gis_map_stores.html`！")


# ====================================================
# 主流程執行
# ====================================================
def main():
    print("🚀 開始執行階段四：全方位數據分析與圖表生成流程...\n")

    analyze_brand_market(df)
    analyze_geographic(df)
    analyze_reputation(df)
    build_gis_map(df)
    analyze_cross_dimensions(df)

    print(
        "\n🎉 全數 5 大面向圖表皆已產出！HTML 檔案可直接開啟查看！"
    )


if __name__ == "__main__":
    main()