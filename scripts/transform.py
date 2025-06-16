import pandas as pd

def transform_exchange_data(df: pd.DataFrame) -> pd.DataFrame:
    # 移除缺失值
    df = df.dropna()

    # 確保 rate 欄位是 float 類型
    df["rate"] = df["rate"].astype(float)

    # 新增：反向匯率欄位
    df["inverse_rate"] = round(1 / df["rate"], 6)

    # 欄位順序整理
    df = df[["date", "base", "currency", "rate", "inverse_rate"]]

    return df

if __name__ == "__main__":
    # 測試用：從 extract 的 CSV 讀進來再轉換
    df_raw = pd.read_csv("data/latest.csv")
    df_transformed = transform_exchange_data(df_raw)

    print("轉換後的資料：")
    print(df_transformed)
