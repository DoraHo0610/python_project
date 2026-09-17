import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv("./.env", override=True)

# 1. 設定本機 MySQL 連線資訊(從環境變數讀取，勿寫死於程式碼中）
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_DB = os.environ.get("MYSQL_DB", "wowprime")


mysql_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
mysql_engine = create_engine(mysql_url)

# 2. 設定 Supabase PostgreSQL 連線資訊(從環境變數讀取，勿寫死於程式碼中）
PG_USER = os.environ.get("PG_USER", "")
PG_PASSWORD = os.environ.get("PG_PASSWORD", "")
PG_HOST = os.environ.get("PG_HOST", "")
PG_PORT = int(os.environ.get("PG_PORT", 6543))
PG_DB = os.environ.get("PG_DB", "postgres")

pg_url = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
pg_engine = create_engine(pg_url)

# 3. 讀取 MySQL 資料表並寫入 Supabase
tables = ["brands", "stores"]  # 若有其他資料表，可加在陣列中如 ["brands", "stores"]



for table_name in tables:
    print(f"正在搬移 {table_name} 資料表...")
    # 從 MySQL 撈取全部資料
    df = pd.read_sql(f"SELECT * FROM {table_name}", mysql_engine)

    # 自動在 Supabase 建表並寫入資料
    df.to_sql(
        table_name, pg_engine, if_exists="replace", index=False
    )
    print(f"✅ {table_name} 搬移完成！")