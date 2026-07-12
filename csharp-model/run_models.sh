#!/bin/bash

# Run regression model
echo "Running Regression Model..."
mlnet regression \
    --dataset "Indicator_1h.csv" \
    --label-col 4 \
    --has-header true \
    --name RegressionModelClose \
    --train-time 60

# Find and copy MLModel.zip for regression
find /app -name MLModel.zip -exec cp {} /app/RegressionModelClose/RegressionModelClose.ConsoleApp/ \;

# Rename ModelBuilder.cs for regression
mv ./RegressionModelClose/RegressionModelClose.ConsoleApp/ModelBuilder.cs ./RegressionModelClose/RegressionModelClose.ConsoleApp/RegressionModelBuilder.cs

# Run time series forecasting model (using regression with time series options)
echo "Running Second Regression Forecasting Model..."
mlnet regression \
    --dataset "Indicator_1h.csv" \
    --label-col 4 \
    --has-header true \
    --name RegressionModelCloseLong \
    --train-time 120

# Find and copy MLModel.zip for time series
find /app -name MLModel.zip -exec cp {} /app/RegressionModelCloseLong/RegressionModelCloseLong.ConsoleApp/ \;

# Rename ModelBuilder.cs for time series
mv ./RegressionModelCloseLong/RegressionModelCloseLong.ConsoleApp/ModelBuilder.cs ./RegressionModelCloseLong/RegressionModelCloseLong.ConsoleApp/RegressionModelCloseLong.cs

# Build and run regression model
echo "Building and Running Regression Model..."
cd /app/RegressionModelClose/RegressionModelClose.ConsoleApp
dotnet build
dotnet run

# Build and run time series model
echo "Building and Running Time Series Model..."
cd /app/RegressionModelCloseLong/RegressionModelCloseLong.ConsoleApp
dotnet build
dotnet run

echo "Models execution completed."