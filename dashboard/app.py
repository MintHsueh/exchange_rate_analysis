# import streamlit as st
# import pandas as pd
# import psycopg2
# import os
# from dotenv import load_dotenv
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates

# # 載入環境變數
# load_dotenv()

# # PostgreSQL 連線設定
# conn = psycopg2.connect(
#     dbname=os.getenv("PG_DATABASE"),
#     user=os.getenv("PG_USER"),
#     password=os.getenv("PG_PASSWORD"),
#     host=os.getenv("PG_HOST"),
#     port=os.getenv("PG_PORT")
# )

# # 頁面標題
# st.title("💱 匯率分析 Dashboard")

# # 查詢所有資料
# df = pd.read_sql("SELECT * FROM exchange_rate_analysis ORDER BY date", conn)

# # 幣別下拉選單
# currencies = df["currency"].unique().tolist()
# selected_currency = st.selectbox("選擇幣別", currencies)

# # 篩選特定幣別資料
# df_selected = df[df["currency"] == selected_currency]

# # 畫圖
# st.subheader(f"{selected_currency} 匯率與 7 日移動平均")
# fig, ax = plt.subplots()
# ax.plot(df_selected["date"], df_selected["rate"], label="Rate", marker="o")

# # 為每個資料點標註日期
# for x, y in zip(df_selected["date"], df_selected["rate"]):
#     ax.text(x, y, x.strftime('%m/%d'), fontsize=7, rotation=0, ha='left', va='bottom')


# ax.plot(df_selected["date"], df_selected["moving_avg_7d"], label="7D Moving Avg", linestyle="--")
# ax.set_xlabel("日期")
# ax.set_ylabel("匯率")
# ax.legend()

# # 清理 X 軸日期格式
# # ax.xaxis.set_major_locator(mdates.AutoDateLocator())
# ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))  # 每 5 天顯示一次
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
# plt.xticks(rotation=45)

# st.pyplot(fig)

# # 顯示 z-score、漲跌幅資料表
# st.subheader(f"{selected_currency} - 詳細分析指標")
# st.dataframe(df_selected[["date", "rate", "prev_rate", "change_percent", "z_score"]].set_index("date"))
# #---

# # Z-score 異常偵測圖
# st.subheader(f"{selected_currency} - Z-score 異常偵測")

# # 自訂 Z-score 閾值（可互動調整）
# z_threshold = st.slider("設定異常 z-score 閾值", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

# # 畫圖
# fig2, ax2 = plt.subplots()
# ax2.plot(df_selected["date"], df_selected["z_score"], label="Z-Score", marker="o")

# # 閾值線
# ax2.axhline(y=z_threshold, color='red', linestyle='--', label=f"+{z_threshold}")
# ax2.axhline(y=-z_threshold, color='red', linestyle='--', label=f"-{z_threshold}")
# ax2.axhline(y=0, color='gray', linestyle='--')

# # 異常點
# outliers = df_selected[(df_selected["z_score"] > z_threshold) | (df_selected["z_score"] < -z_threshold)]
# ax2.scatter(outliers["date"], outliers["z_score"], color='red', label="Outliers")

# # 標註異常日期
# for x, y in zip(outliers["date"], outliers["z_score"]):
#     ax2.text(x, y, x.strftime('%m/%d'), fontsize=7, color='red', ha='left', va='bottom')

# ax2.set_xlabel("日期")
# ax2.set_ylabel("Z-score")
# ax2.set_title(f"{selected_currency} Z-score 異常偵測")
# ax2.legend()
# plt.xticks(rotation=45)

# st.pyplot(fig2)


#========================================================================================

import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# 載入環境變數
load_dotenv()

# PostgreSQL 連線
conn = psycopg2.connect(
    dbname=os.getenv("PG_DATABASE"),
    user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT")
)

# 頁面主標題
st.markdown("<h1 style='color:#ff4b4b;'> 匯率分析 Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# 讀取資料
df = pd.read_sql("SELECT * FROM exchange_rate_analysis ORDER BY date", conn)

# 側邊欄選項
st.sidebar.header("設定選項")
currencies = df["currency"].unique().tolist()
selected_currency = st.sidebar.selectbox("選擇幣別", currencies)

# 篩選資料
df_selected = df[df["currency"] == selected_currency].copy()
df_selected["date"] = pd.to_datetime(df_selected["date"])

# 匯率走勢 + 移動平均圖（Plotly）
st.subheader(f"{selected_currency} 匯率走勢")
fig_rate = go.Figure()
fig_rate.add_trace(go.Scatter(x=df_selected["date"], y=df_selected["rate"],
                              mode='lines+markers', name='匯率'))
fig_rate.add_trace(go.Scatter(x=df_selected["date"], y=df_selected["moving_avg_7d"],
                              mode='lines', name='7日移動平均', line=dict(dash='dash')))
fig_rate.update_layout(xaxis_title='date', yaxis_title='匯率', height=400)
st.plotly_chart(fig_rate)

# Z-score 異常偵測圖
st.subheader(f"{selected_currency} Z-score 異常點")
fig_z = px.line(df_selected, x="date", y="z_score", title="Z-score 趨勢")
# 加上異常點
df_anomaly = df_selected[(df_selected["z_score"] > 1.5) | (df_selected["z_score"] < -1.5)]
fig_z.add_trace(go.Scatter(x=df_anomaly["date"], y=df_anomaly["z_score"],
                           mode="markers", name="異常", marker=dict(color="red", size=10)))
fig_z.update_layout(height=400)
st.plotly_chart(fig_z)

# 顯示詳細資料表格
st.subheader("詳細分析指標（含漲跌幅 & Z-score）")

# 可加條件變色
def highlight_zscore(val):
    if val > 1.5 or val < -1.5:
        return 'background-color: #ffcccc'
    return ''

styled_df = df_selected[["date", "rate", "prev_rate", "change_percent", "z_score"]].style.applymap(highlight_zscore, subset=["z_score"])

st.dataframe(styled_df)
