# Mount Data Lake
dbutils.fs.mount(
  source = "wasbs://bronze@$storageAccountName.blob.core.windows.net/",
  mount_point = "/mnt/bronze",
  extra_configs = {"fs.azure.account.key.$storageAccountName.blob.core.windows.net": dbutils.secrets.get(scope="your-scope", key="storage-key")}
)
dbutils.fs.mount(
  source = "wasbs://silver@$storageAccountName.blob.core.windows.net/",
  mount_point = "/mnt/silver",
  extra_configs = {"fs.azure.account.key.$storageAccountName.blob.core.windows.net": dbutils.secrets.get(scope="your-scope", key="storage-key")}
)

# Transform: Read from Bronze, clean, write to Silver
df = spark.read.json("/mnt/bronze/sales/*.json")
cleaned_df = df.na.drop().dropDuplicates()
cleaned_df.write.parquet("/mnt/silver/sales/")

