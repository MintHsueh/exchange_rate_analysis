from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, lag, round, avg, stddev, when, max as spark_max, expr
from pyspark.sql.window import Window
import os
from dotenv import load_dotenv

# 建立 SparkSession
spark = SparkSession.builder \
    .appName("Exchange Rate Analysis") \
    .config("spark.jars", os.path.abspath("jars/postgresql-42.6.0.jar")) \
    .config("spark.driver.extraClassPath", os.path.abspath("jars/postgresql-42.6.0.jar")) \
    .config("spark.executor.extraClassPath", os.path.abspath("jars/postgresql-42.6.0.jar")) \
    .getOrCreate()

# 載入 .env 設定
load_dotenv()
user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")
db = os.getenv("PG_DATABASE")

jdbc_url = f"jdbc:postgresql://{host}:{port}/{db}"

# 讀取 exchange_rates 全部資料
df_all = spark.read \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "exchange_rates") \
    .option("user", user) \
    .option("password", password) \
    .load()

# 確保日期是 date 格式
df_all = df_all.withColumn("date", to_date("date", "yyyy-MM-dd"))

# 讀取已分析表的最大日期（每個幣別）
df_analyzed = spark.read \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "exchange_rate_analysis") \
    .option("user", user) \
    .option("password", password) \
    .load()

max_date_df = df_analyzed.groupBy("currency").agg(spark_max("date").alias("last_date"))

# inner join 原始資料與 max_date 資訊，用來篩選尚未分析的資料（保留每幣別最新後7筆）
df_joined = df_all.join(max_date_df, on="currency", how="left")

# 篩選出大於最後分析日期的資料（含前6天）
df_filtered = df_joined.filter((col("last_date").isNull()) | (col("date") > col("last_date") - expr("INTERVAL 7 DAYS")))

# 建立 window
lag_window = Window.partitionBy("currency").orderBy("date")
moving_window = lag_window.rowsBetween(-6, 0)

# 計算漲跌幅
df_filtered = df_filtered.withColumn("prev_rate", lag("rate").over(lag_window))
df_filtered = df_filtered.withColumn("change_percent", round((col("rate") - col("prev_rate")) / col("prev_rate") * 100, 4))

# 計算移動平均與波動率
df_filtered = df_filtered.withColumn("moving_avg_7d", avg("rate").over(moving_window))
df_filtered = df_filtered.withColumn("volatility_7d", stddev("rate").over(moving_window))

# 加入 Z-score（避免除以零）
df_filtered = df_filtered.withColumn(
    "z_score",
    when(col("volatility_7d") == 0, None).otherwise((col("rate") - col("moving_avg_7d")) / col("volatility_7d"))
)

# 最終只輸出尚未分析的資料
final_df = df_filtered.filter((col("last_date").isNull()) | (col("date") > col("last_date")))

# 寫入 PostgreSQL 的 exchange_rate_analysis 表
final_df.select(
    "date", "currency", "rate", "prev_rate", "change_percent", "moving_avg_7d", "volatility_7d", "z_score"
).write \
    .format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "exchange_rate_analysis") \
    .option("user", user) \
    .option("password", password) \
    .option("driver", "org.postgresql.Driver") \
    .mode("append") \
    .save()