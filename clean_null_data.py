import getpass
import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ====================================================
# 載入 .env 設定並建立資料庫連線
# ====================================================
load_dotenv("./.env", override=True)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER") or input("DB user: ")
DB_PASSWORD = os.environ.get("DB_PASSWORD") or getpass.getpass("DB password: ")
DB_NAME = os.environ.get("DB_NAME", "wowprime")

engine_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
engine = create_engine(engine_url)


# ====================================================
# 從資料庫讀取資料
# ====================================================
def load_data_from_db():
    print("🔍 正在連線資料庫並讀取 `stores` 資料表...")
    query = "SELECT * FROM stores;"
    df = pd.read_sql(query, engine)
    print(f"✅ 成功載入 {len(df)} 筆資料！\n")
    return df


# # ====================================================
# # 診斷缺失值 (Null / NaN)
# # ====================================================
def inspect_null_values(df):
    print("=" * 60)
    print("📊【1. 各欄位 Null 值統計報表】")
    print("=" * 60)

    # 計算各欄位 Null 數量與百分比
    null_count = df.isnull().sum()
    null_percentage = (df.isnull().sum() / len(df)) * 100

    null_summary = pd.DataFrame(
        {
            "資料型態": df.dtypes,
            "Null總數": null_count,
            "Null比例 (%)": null_percentage.round(2),
        }
    )

    # 只顯示有 Null 的欄位
    null_summary_filtered = null_summary[null_summary["Null總數"] > 0]

    if null_summary_filtered.empty:
        print("🎉 太棒了！你的資料表中沒有任何 Null 值！")
        return False
    else:
        print(null_summary_filtered)
        print("=" * 60)

        # 找出至少包含一個 Null 值的完整列 (Rows)
        rows_with_null = df[df.isnull().any(axis=1)]
        print(f"\n⚠️ 共有 {len(rows_with_null)} 筆門市資料包含 Null 值。")
        print("\n前 5 筆包含 Null 值的門市預覽：")
        # 顯示主要辨識欄位與有問題的欄位
        preview_cols = [
            c
            for c in ["store_id", "brand", "full_name"]
            if c in rows_with_null.columns
        ] + list(null_summary_filtered.index)
        print(rows_with_null[preview_cols].head())

        return True


raw_df = load_data_from_db()
has_null = inspect_null_values(raw_df)
print(raw_df.info())

# ====================================================
# 4. 資料清理邏輯 (依需求進行填補或處置)
# ====================================================
# def clean_data(df):
#     print("\n" + "=" * 60)
#     print("🧹【2. 開始執行資料清理與填補流程】")
#     print("=" * 60)

#     df_cleaned = df.copy()

#     # --- 策略 A: 文字欄位填補 ---
#     # 若價位區間 price_range 為 Null，填入 "未提供"
#     if "price_range" in df_cleaned.columns:
#         df_cleaned["price_range"] = df_cleaned["price_range"].fillna("未提供")
#         print("  ✓ 已將 `price_range` 的 Null 填補為 '未提供'")

#     # --- 策略 B: 數值欄位填補 ---
#     # 若 avg_price 為 Null，可以填補為該品牌 (brand) 的平均價格，若仍無則填補整體平均值或 0
#     if "avg_price" in df_cleaned.columns and "brand" in df_cleaned.columns:
#         # 使用同品牌 (brand) 的平均價格填補
#         df_cleaned["avg_price"] = df_cleaned.groupby("brand")[
#             "avg_price"
#         ].transform(lambda x: x.fillna(x.mean()))
#         # 若還有剩餘的 Null（例如該品牌全部無價位），補 0
#         df_cleaned["avg_price"] = df_cleaned["avg_price"].fillna(0).round(0)
#         print("  ✓ 已將 `avg_price` 的 Null 依品牌平均值進行填補")

#     # 若評分 / 評論數為 Null，補 0
#     if "google_rating" in df_cleaned.columns:
#         df_cleaned["google_rating"] = df_cleaned["google_rating"].fillna(0.0)
#         print("  ✓ 已將 `google_rating` 的 Null 填補為 0.0")

#     if "google_review_count" in df_cleaned.columns:
#         df_cleaned["google_review_count"] = (
#             df_cleaned["google_review_count"].fillna(0).astype(int)
#         )
#         print("  ✓ 已將 `google_review_count` 的 Null 填補為 0")

#     # --- 策略 C: 刪除關鍵欄位為 Null 的列 ---
#     # 如果經緯度 latitude/longitude 為 Null 且無法補齊，可選擇刪除該列（此處示範保留，僅印出警告）
#     if (
#         "latitude" in df_cleaned.columns
#         and "longitude" in df_cleaned.columns
#     ):
#         missing_geo = df_cleaned[
#             df_cleaned["latitude"].isnull() | df_cleaned["longitude"].isnull()
#         ]
#         if not missing_geo.empty:
#             print(
#                 f"  ⚠️ 注意: 仍有 {len(missing_geo)} 筆資料缺少經緯度座標 (Latitude/Longitude)"
#             )

#     return df_cleaned

















# ====================================================
# 5. 主流程執行與結果儲存
# ====================================================
# def main():
#     # 1. 讀取資料
#     raw_df = load_data_from_db()

#     # 2. 檢視與診斷 Null 值
#     has_null = inspect_null_values(raw_df)

#     if has_null:
#         # 3. 執行清理
#         cleaned_df = clean_data(raw_df)

#         # 4. 匯出清理後的結果為 CSV 備份
#         output_csv = "stores_cleaned.csv"
#         cleaned_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
#         print(f"\n🎉 資料清理完成！已將清洗後的檔案存至: {output_csv}")

#         # 5. (可選) 覆蓋或回寫回資料庫新表 `stores_cleaned`
#         # cleaned_df.to_sql("stores_cleaned", engine, if_exists="replace", index=False)
#         # print("🎉 已將清理後的資料寫入資料庫 `stores_cleaned` 表格中！")
#     else:
#         print("\n資料狀態良好，無須額外清理！")


# if __name__ == "__main__":
#     main()