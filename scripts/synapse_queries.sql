CREATE EXTERNAL TABLE GoldSales (
    ProductID INT,
    TotalQuantity INT,
    TotalSales FLOAT
) WITH (
    LOCATION = 'gold/sales_aggregated/',
    DATA_SOURCE = AzureDataLake,  -- Create data source first
    FILE_FORMAT = ParquetFormat
);

-- KPI Query
SELECT ProductCategory, SUM(TotalSales) FROM GoldSales GROUP BY ProductCategory;
