import requests
import pandas as pd
from datetime import datetime
import os

def fetch_exchange_rates(base_currency="TWD", target_currencies=["USD", "JPY", "EUR", "GBP"]):
    url = f"https://open.er-api.com/v6/latest/{base_currency}"
    response = requests.get(url)
    data = response.json()

    print("API 回傳內容：", data)  # Debug 用

    if data.get("result") != "success":
        raise ValueError("API 回傳失敗，請檢查網址或網路")

    rates = data["rates"]
    today = datetime.today().strftime("%Y-%m-%d")

    records = []
    for currency in target_currencies:
        if currency in rates:
            records.append({
                "date": today,
                "base": base_currency,
                "currency": currency,
                "rate": rates[currency]
            })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    df = fetch_exchange_rates()
    print(df)

    # Optional：存檔做資料備份
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/latest.csv", index=False)
