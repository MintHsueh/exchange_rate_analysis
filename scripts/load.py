import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from sqlalchemy import text
from datetime import datetime

def load_to_postgresql(df: pd.DataFrame):
    # 載入 .env 裡的資料庫資訊
    load_dotenv()
    user = os.getenv("PG_USER")
    password = os.getenv("PG_PASSWORD")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    db = os.getenv("PG_DATABASE")

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(db_url)

    # # 強制先刪掉資料表
    # with engine.begin() as conn:
    #     conn.execute(text("DROP TABLE IF EXISTS exchange_rates"))

    df["processed_at"] = datetime.now()

    # 將資料寫入 exchange_rates 表，若已存在就附加
    df.to_sql("exchange_rates", engine, if_exists="append", index=False)
    # df.to_sql("exchange_rates", con=engine, if_exists="replace", index=False)
    print("資料已寫入 PostgreSQL")

if __name__ == "__main__":
    from transform import transform_exchange_data

    # 讀取 CSV → 清理 → 寫入 DB
    df_raw = pd.read_csv("data/latest.csv")
    df_cleaned = transform_exchange_data(df_raw)
    load_to_postgresql(df_cleaned)

