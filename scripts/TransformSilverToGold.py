# Mount Data Lake
dbutils.fs.mount(
  source = "wasbs://silver@$storageAccountName.blob.core.windows.net/",
  mount_point = "/mnt/silver",
  extra_configs = {"fs.azure.account.key.$storageAccountName.blob.core.windows.net": dbutils.secrets.get(scope="your-scope", key="storage-key")}
)
dbutils.fs.mount(
  source = "wasbs://gold@$storageAccountName.blob.core.windows.net/",
  mount_point = "/mnt/gold",
  extra_configs = {"fs.azure.account.key.$storageAccountName.blob.core.windows.net": dbutils.secrets.get(scope="your-scope", key="storage-key")}
)

# Transform: Read from Silver, aggregate, write to Gold
df = spark.read.parquet("/mnt/silver/sales/")
aggregated_df = df.groupBy("productID").agg({"quantity": "sum", "price": "sum"})
aggregated_df.write.parquet("/mnt/gold/sales_aggregated/")
