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
# 🎯 修改重點 1：多撈取 established_year 與 product_type 欄位
query = """
SELECT 
    s.*, 
    b.brand_name,
    b.brand_name2,
    b.established_year,
    b.product_type
FROM stores s
LEFT JOIN brands b ON s.brand_id = b.brand_id
WHERE s.status = '營業中';
"""
df = pd.read_sql(query, engine)

# ====================================================
# 資料預處理防錯
# ====================================================
# 1. 若 google_rating 或是 google_review_count 有 null 值，移除該列資料
df = df.dropna(subset=["google_rating", "google_review_count"])

# 2. 刪除 google_place_id 欄位 (若存在的話)
if "google_place_id" in df.columns:
    df = df.drop(columns=["google_place_id"])

# 其他欄位基礎預處理
df["avg_price"] = df["avg_price"].fillna(0)
df["brand_name"] = df["brand_name"].fillna("未知品牌")
df["product_type"] = df["product_type"].fillna("其他類型")


print(f"✅ 成功載入並清理完成！共獲取 {len(df)} 筆有效分析資料！\n")


# ====================================================
# 面向 1-1：品牌與市場佈局分析 (Brand & Market Distribution)
# ====================================================


def analyze_brand_market(df):
    print("📊 執行 [面向 1-1]：品牌門市規模與評分分佈分析...")

    # 1.1 品牌門市數量排行榜
    brand_counts = df["brand_name"].value_counts().reset_index()
    brand_counts.columns = ["brand_name", "store_count"]

    fig1 = px.bar(
        brand_counts,
        x="brand_name",
        y="store_count",
        title="王品集團各品牌門市數量統計長條圖",
        labels={"brand_name": "品牌名稱", "store_count": "門市數量"},
        color="store_count",
        color_continuous_scale="Purpor",
        text="store_count",
    )

    fig1.update_traces(textfont=dict(size=14))

    fig1.update_layout(
        template="plotly_white",
        title=dict(font=dict(size=22)),
        xaxis=dict(
            categoryorder="total descending",
            tickangle=-45,
            title=dict(text="品牌名稱", font=dict(size=18)),
            tickfont=dict(size=16),
        ),
        yaxis=dict(
            title=dict(text="門市數量", font=dict(size=18)),
            tickfont=dict(size=15),
        ),
        margin=dict(b=120),
    )

    fig1.write_html("chart1-1_brand_store_counts.html")

    # ---------------------------------------------------------
    # 🎯 新增 1.2 圖表：品牌門市數量 vs. 成立年份相關性分析 (Scatter + OLS)
    # ---------------------------------------------------------
    print("📊 執行 [面向 1-2]：品牌門市數量與成立年份相關性分析...")

    # 以品牌進行聚合，計算各品牌的門市數量與成立年份
    brand_summary = (
        df.groupby(["brand_name", "brand_name2"])
        .apply(
            lambda g: pd.Series({
                "store_count": len(g),
                "established_year": (
                    g["established_year"].iloc[0]
                    if pd.notnull(g["established_year"].iloc[0])
                    else np.nan
                ),
            }),
            include_groups=False,
        )
        .reset_index()
    )

    # 過濾有有效成立年份資料的品牌
    valid_year_brands = brand_summary.dropna(
        subset=["established_year"]
    ).copy()

    if not valid_year_brands.empty:
        fig15 = px.scatter(
            valid_year_brands,
            x="established_year",
            y="store_count",
            text="brand_name2",
            size="store_count",
            color="brand_name",
            trendline="ols",
            trendline_scope="overall",
            title="<b>王品集團各品牌門市數量與成立年份相關性分析</b>",
            labels={
                "established_year": "品牌成立年份",
                "store_count": "門市數量",
                "brand_name": "品牌名稱",
            },
            hover_data={
                "established_year": ":d",
                "store_count": True,
            },
            template="plotly_white",
            height=750,
        )

        fig15.update_traces(
            textposition="top center", textfont=dict(size=12)
        )
        fig15.update_layout(
            title=dict(font=dict(size=22)),
            xaxis=dict(
                title=dict(text="品牌成立年份 (Year)", font=dict(size=18)),
                tickfont=dict(size=14),
                dtick=5,  # X 軸每 5 年為一格刻度
            ),
            yaxis=dict(
                title=dict(text="門市數量 (家)", font=dict(size=18)),
                tickfont=dict(size=14),
            ),
            legend=dict(
                title=dict(text="品牌名稱", font=dict(size=16)),
                font=dict(size=13),
            ),
        )

        fig15.write_html("chart1-2_store_count_vs_year.html")
    else:
        print(
            "⚠️ 警告：缺少品牌成立年份資料，跳過 chart1-2 圖表繪製。"
        )


# ====================================================
# 面向 1-3：地理區域與展店策略分析 (Geographic Analysis)
# ====================================================
def analyze_geographic(df):
    print("📊 執行 [面向 1-3]：縣市門市密度與區域消費力分析...")

    # 1-3 各縣市門市數量分佈
    city_counts = df["city"].value_counts().reset_index()
    city_counts.columns = ["city", "store_count"]

    sum6=city_counts[city_counts["city"].isin(["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"])]["store_count"].sum()
    print(f"📊 六都門市總數: {sum6} 家，占全台門市總數 {len(df)} 家的比例為 {sum6/len(df)*100:.2f}%")

    fig1 = px.pie(
        city_counts,
        values="store_count",
        names="city",
        title="王品集團全台門市縣市分佈比例圓餅圖",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    # fig1.update_layout(
    #     template="plotly_white",
    #     title=dict(font=dict(size=24)),
    #     legend=dict(font=dict(size=16)),
    # )

    # 🌟 修改設定文字標籤外擴並顯示引導線
    fig1.update_traces(
        textposition="outside",          # 標籤放於圓餅圖外部（Plotly 會自動繪製引導線）
        textinfo="label+percent",        # 顯示格式：縣市名稱 + 百分比 (例：台北市: 25.0%)
        outsidetextfont=dict(size=14),   # 設定外部文字標籤大小
    )

    fig1.update_traces(insidetextfont=dict(size=15))
    fig1.write_html("chart1-3_city_distribution_piechart.html")
    



# ====================================================
# 面向 1-4 縣市 x 品牌門市數量熱力圖
# ====================================================


    # 1-4 縣市 x 品牌門市數量熱力圖 (Heatmap)
    print("📊 執行 [面向 1-4]：縣市 x 品牌門市數量熱力圖 ...")

    # 1. 建立交叉表
    city_brand_pivot = pd.crosstab(df["city"], df["brand_name"])

    # 🌟 關鍵修改：計算各縣市總門市數，並依照總門市數「由大到小」重新排序列表索引
    city_order = city_brand_pivot.sum(axis=1).sort_values(ascending=False).index
    city_brand_pivot = city_brand_pivot.loc[city_order]

    fig2 = px.imshow(
        city_brand_pivot,
        labels=dict(x="品牌名稱", y="縣市", color="門市數"),
        x=city_brand_pivot.columns,
        y=city_brand_pivot.index,
        title="王品集團各縣市門市品牌佈局熱力矩陣圖",
        color_continuous_scale="YlOrRd",
        text_auto=True,
    )

    fig2.update_layout(
        template="plotly_white",
        title=dict(font=dict(size=22)),
        xaxis=dict(
            title=dict(text="品牌名稱", font=dict(size=18)),
            tickfont=dict(size=13),
            tickangle=-45,
        ),
        yaxis=dict(
            title=dict(text="縣市", font=dict(size=18)),
            tickfont=dict(size=14),
            autorange="reversed",  # 🌟 關鍵設定：讓門市數量最多的縣市排在熱力圖的最上方 (Top 1)
        ),
        coloraxis_colorbar=dict(
            title=dict(text="門市數", font=dict(size=16)),
            tickfont=dict(size=14),
        ),
        margin=dict(b=120),
    )

    fig2.update_traces(textfont=dict(size=13))
    fig2.write_html("chart1-4_city_brand_heatmap.html")


# ====================================================
# 面向 2：各品牌Google評分分析
# ====================================================
def analyze_reputation(df):
    print("📊 執行 [面向 2-1]：評分 vs. 評論數四象限矩陣分析...")

    median_reviews = df["google_review_count"].median()
    median_rating = df["google_rating"].median()

    # 2.1 評分 (X軸) vs. 評論數 (Y軸) 四象限圖
    fig = px.scatter(
        df,
        x="google_rating",
        y="google_review_count",
        color="brand_name",
        hover_name="full_name",
        hover_data=["city", "avg_price"],
        title=f"王品集團各門市Google評分四象限圖 (評分中位數: {median_rating}, 評論數中位數: {int(median_reviews)})",
        labels={
            "google_rating": "Google 評分 (1-5)",
            "google_review_count": "Google 評論總數",
            "brand_name": "品牌名稱",
        },
    )

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
            title=dict(text="Google 評分 (1-5)", font=dict(size=18)),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title=dict(text="Google 評論總數", font=dict(size=18)),
            tickfont=dict(size=14),
        ),
        legend=dict(
            title=dict(text="品牌名稱", font=dict(size=16)),
            font=dict(size=14),
        ),
    )

    fig.write_html("chart2-1_rating_scatter_plot.html")

    # 2-2 各品牌評分區間分佈 (Box Plot)
    print("📊 執行 [面向 2-2]：王品集團各品牌Google評分盒狀圖...")
    fig2 = px.box(
        df,
        x="brand_name",
        y="google_rating",
        color="brand_name",
        title="王品集團各品牌Google評分盒狀圖",
        labels={"google_rating": "Google 評分", "brand_name": "品牌名稱"},
    )

    fig2.update_layout(
        showlegend=False,
        template="plotly_white",
        title=dict(font=dict(size=22)),
        xaxis=dict(
            title=dict(text="品牌名稱", font=dict(size=18)),
            tickfont=dict(size=16),
            tickangle=-45,
        ),
        yaxis=dict(
            title=dict(text="Google 評分", font=dict(size=18)),
            tickfont=dict(size=14),
        ),
        margin=dict(b=130),
    )

    fig2.write_html("chart2-2_brand_rating_boxplot.html")


# ====================================================
# 面向 2-3：品牌加權評分與平均客單價相關性分析
# ====================================================
def analyze_cross_dimensions(df):
    print("📊 執行 [面向 2-3]：品牌加權評分與平均客單價相關性分析圖...")

    # 防呆機制：過濾客單價與評分大於 0 的有效門市資料
    valid_price_df = df[
        (df["avg_price"] > 0) & (df["google_rating"] > 0)
    ].copy()

    if valid_price_df.empty:
        print("⚠️ 警告：沒有找到有效的門市資料，跳過面向 2-3 分析。")
        return

    # 1. 以品牌為單位聚合計算：加權評分、平均客單價、成立年份、總評論數與門市數量
    brand_summary = (
        valid_price_df.groupby(["brand_name", "brand_name2"])
        .apply(
            lambda g: pd.Series({
                "weighted_rating": (
                    (g["google_rating"] * g["google_review_count"]).sum()
                    / g["google_review_count"].sum()
                    if g["google_review_count"].sum() > 0
                    else 0
                ),
                "avg_price": g["avg_price"].mean(),
                "established_year": (
                    g["established_year"].iloc[0]
                    if pd.notnull(g["established_year"].iloc[0])
                    else np.nan
                ),
                "product_type": (
                    g["product_type"].iloc[0]
                    if pd.notnull(g["product_type"].iloc[0])
                    else "其他類型"
                ),
                "total_reviews": g["google_review_count"].sum(),
                "store_count": len(g),
            }),
            include_groups=False,
        )
        .reset_index()
    )

    # 四捨五入與格式清理
    brand_summary["weighted_rating"] = brand_summary["weighted_rating"].round(
        2
    )
    brand_summary["avg_price"] = brand_summary["avg_price"].round(0)

    # ---------------------------------------------------------
    # 2-3 品牌加權評分與平均客單價相關性分析圖
    # ---------------------------------------------------------
    fig = px.scatter(
        brand_summary,
        x="avg_price",
        y="weighted_rating",
        text="brand_name2",
        size="store_count",
        color="brand_name",
        trendline="ols",
        trendline_scope="overall",
        title="<b>王品集團各品牌'Google加權平均分數'與'平均客單價'相關性分析</b>",
        labels={
            "avg_price": "品牌平均客單價 (NTD)",
            "weighted_rating": "加權平均 Google 評分",
            "brand_name": "品牌名稱",
            "store_count": "門市數量",
        },
        hover_data={
            "avg_price": ":$.0f",
            "weighted_rating": ":.2f",
            "store_count": True,
            "total_reviews": ":,",
        },
        template="plotly_white",
        height=750,
    )

    fig.update_traces(textposition="top center", textfont=dict(size=12))
    fig.update_layout(
        title=dict(font=dict(size=22)),
        xaxis=dict(
            title=dict(text="品牌平均客單價 (NTD)", font=dict(size=18)),
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title=dict(text="加權平均 Google 評分", font=dict(size=18)),
            tickfont=dict(size=14),
            range=[3.8, 5.0],
        ),
        legend=dict(
            title=dict(text="品牌名稱", font=dict(size=16)),
            font=dict(size=13),
        ),
    )

    html_path = "chart2-3_price_vs_rating_overall.html"
    fig.write_html(html_path)

    # ---------------------------------------------------------
    # 🎯 延伸圖表代號 chart2-4：品牌加權評分與成立年份相關性分析 (px.scatter + OLS)
    # ---------------------------------------------------------
    # 過濾有有效成立年份的品牌資料
    print("📊 執行 [面向 2-4]：品牌加權評分與成立年份相關性分析圖...")
    valid_year_brands = brand_summary.dropna(
        subset=["established_year"]
    ).copy()

    if not valid_year_brands.empty:
        fig_1 = px.scatter(
            valid_year_brands,
            x="established_year",
            y="weighted_rating",
            text="brand_name2",
            size="store_count",
            color="brand_name",
            trendline="ols",
            trendline_scope="overall",
            title="<b>王品集團各品牌'Google加權平均分數'與'成立年份'相關性分析</b>",
            labels={
                "established_year": "品牌成立年份",
                "weighted_rating": "加權平均 Google 評分",
                "brand_name": "品牌名稱",
                "store_count": "門市數量",
            },
            hover_data={
                "established_year": ":d",
                "weighted_rating": ":.2f",
                "store_count": True,
            },
            template="plotly_white",
            height=750,
        )

        fig_1.update_traces(textposition="top center", textfont=dict(size=12))
        fig_1.update_layout(
            title=dict(font=dict(size=22)),
            xaxis=dict(
                title=dict(text="品牌成立年份 (Year)", font=dict(size=18)),
                tickfont=dict(size=14),
                dtick=5,  # X 軸每 5 年為一格刻度
            ),
            yaxis=dict(
                title=dict(text="加權平均 Google 評分", font=dict(size=18)),
                tickfont=dict(size=14),
                range=[3.8, 5.0],
            ),
            legend=dict(
                title=dict(text="品牌名稱", font=dict(size=16)),
                font=dict(size=13),
            ),
        )

        html_1_path = "chart2-4_year_vs_rating.html"
        fig_1.write_html(html_1_path)

    else:
        print(
            "⚠️ 警告：缺少品牌成立年份資料，跳過 chart2-4 圖表繪製。"
        )

    # ---------------------------------------------------------
    # 🎯 延伸圖表代號 chart2-5：Google 加權平均評分之於餐廳類型盒狀圖 (px.box)
    # ---------------------------------------------------------
    print("📊 執行 [面向 2-5]：Google 加權平均評分之於餐廳類型盒狀圖...")
    fig_2 = px.box(
        brand_summary,
        x="product_type",
        y="weighted_rating",
        color="product_type",
        points="all",  # 顯示盒狀圖旁的各品牌數據點
        hover_name="brand_name",
        title="<b>王品集團各餐廳類型之 Google 加權平均分佈 </b>",
        labels={
            "product_type": "餐廳類型 (餐飲品類)",
            "weighted_rating": "加權平均 Google 評分",
            "brand_name": "品牌名稱",
        },
        template="plotly_white",
        height=750,
    )

    fig_2.update_layout(
        showlegend=False,
        title=dict(font=dict(size=22)),
        xaxis=dict(
            title=dict(text="餐廳類型 (Product Type)", font=dict(size=18)),
            tickfont=dict(size=15),
            tickangle=-30,
        ),
        yaxis=dict(
            title=dict(text="加權平均 Google 評分", font=dict(size=18)),
            tickfont=dict(size=14),
            range=[4.0, 5.0],
        ),
        margin=dict(b=120),
    )

    html_2_path = "chart2-5_type_rating_boxplot.html"
    fig_2.write_html(html_2_path)

    return fig


# ====================================================
# 面向 3：空間地理與聚落分析 (Geospatial GIS Map)
# ====================================================
def build_gis_map(df):
    print("🗺️ 最後執行：建置 GIS 互動式地圖 (Folium)...")

    valid_geo_df = df[
        (df["latitude"].notnull()) & (df["longitude"].notnull())
    ]

    m = folium.Map(location=[23.973875, 120.982025], zoom_start=8)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in valid_geo_df.iterrows():
        rating = row["google_rating"]

        if rating >= 4.7:
            color = "green"
        elif rating >= 4.4:
            color = "blue"
        else:
            color = "red"

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
    analyze_cross_dimensions(df)
    build_gis_map(df)

    print("\n🎉 圖表皆已產出！HTML 檔案可直接開啟查看！")


if __name__ == "__main__":
    main()