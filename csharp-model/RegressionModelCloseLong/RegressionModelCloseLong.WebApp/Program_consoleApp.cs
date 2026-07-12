//*****************************************************************************************
//*                                                                                       *
//* This is an auto-generated file by Microsoft ML.NET CLI (Command-Line Interface) tool. *
//*                                                                                       *
//*****************************************************************************************

using System;
using RegressionModelCloseLong.Model;

namespace RegressionModelCloseLong.ConsoleApp
{
    class Program
    {
        static void Main(string[] args)
        {
            // Create single instance of sample data from first line of dataset for model input
            ModelInput sampleData = new ModelInput()
            {
                Datetime = @"2024-01-31 01:00:00",
                Open = 2035.01F,
                High = 2035.8F,
                Low = 2033.3F,
                Volume = 18815F,
                Volume_Ma = 35179.15F,
                RSI_50 = 0F,
                _K_60 = 0F,
                _D_1 = 0F,
                SMA_60 = 0F,
                _K_240 = 0F,
                SMA_240 = 0F,
                _K_540 = 0F,
                SMA_540 = 0F,
                _K_1380 = 0F,
                SMA_1380 = 0F,
                _K_RSI_15 = 0F,
                _D_RSI_1 = 0F,
                _K_RSI_30 = 0F,
                EMA_100 = 2034.235F,
                _K_above = 0F,
                _K_below = 0F,
                Within_5_ = 0F,
                Price_Above_SMA = 0F,
                Price_Below_SMA = 0F,
                Buy = 0F,
                Sell = 0F,
                Entry_Ind = 0F,
                Exit_Ind = 0F,
            };

            // Make a single prediction on the sample data and print results
            var predictionResult = ConsumeModel.Predict(sampleData);

            Console.WriteLine("Using model to make single prediction -- Comparing actual Close with predicted Close from sample data...\n\n");
            Console.WriteLine($"Datetime: {sampleData.Datetime}");
            Console.WriteLine($"Open: {sampleData.Open}");
            Console.WriteLine($"High: {sampleData.High}");
            Console.WriteLine($"Low: {sampleData.Low}");
            Console.WriteLine($"Volume: {sampleData.Volume}");
            Console.WriteLine($"Volume_Ma: {sampleData.Volume_Ma}");
            Console.WriteLine($"RSI_50: {sampleData.RSI_50}");
            Console.WriteLine($"_K_60: {sampleData._K_60}");
            Console.WriteLine($"_D_1: {sampleData._D_1}");
            Console.WriteLine($"SMA_60: {sampleData.SMA_60}");
            Console.WriteLine($"_K_240: {sampleData._K_240}");
            Console.WriteLine($"SMA_240: {sampleData.SMA_240}");
            Console.WriteLine($"_K_540: {sampleData._K_540}");
            Console.WriteLine($"SMA_540: {sampleData.SMA_540}");
            Console.WriteLine($"_K_1380: {sampleData._K_1380}");
            Console.WriteLine($"SMA_1380: {sampleData.SMA_1380}");
            Console.WriteLine($"_K_RSI_15: {sampleData._K_RSI_15}");
            Console.WriteLine($"_D_RSI_1: {sampleData._D_RSI_1}");
            Console.WriteLine($"_K_RSI_30: {sampleData._K_RSI_30}");
            Console.WriteLine($"EMA_100: {sampleData.EMA_100}");
            Console.WriteLine($"_K_above: {sampleData._K_above}");
            Console.WriteLine($"_K_below: {sampleData._K_below}");
            Console.WriteLine($"Within_5_: {sampleData.Within_5_}");
            Console.WriteLine($"Price_Above_SMA: {sampleData.Price_Above_SMA}");
            Console.WriteLine($"Price_Below_SMA: {sampleData.Price_Below_SMA}");
            Console.WriteLine($"Buy: {sampleData.Buy}");
            Console.WriteLine($"Sell: {sampleData.Sell}");
            Console.WriteLine($"Entry_Ind: {sampleData.Entry_Ind}");
            Console.WriteLine($"Exit_Ind: {sampleData.Exit_Ind}");
            Console.WriteLine($"\n\nPredicted Close: {predictionResult.Score}\n\n");
            Console.WriteLine("=============== End of process, hit any key to finish ===============");
            Console.ReadKey();
        }
    }
}
