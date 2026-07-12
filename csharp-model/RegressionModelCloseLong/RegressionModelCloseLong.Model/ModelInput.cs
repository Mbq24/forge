//*****************************************************************************************
//*                                                                                       *
//* This is an auto-generated file by Microsoft ML.NET CLI (Command-Line Interface) tool. *
//*                                                                                       *
//*****************************************************************************************

using Microsoft.ML.Data;

namespace RegressionModelCloseLong.Model
{
    public class ModelInput
    {
        [ColumnName("Datetime"), LoadColumn(0)]
        public string Datetime { get; set; }


        [ColumnName("Open"), LoadColumn(1)]
        public float Open { get; set; }


        [ColumnName("High"), LoadColumn(2)]
        public float High { get; set; }


        [ColumnName("Low"), LoadColumn(3)]
        public float Low { get; set; }


        [ColumnName("Close"), LoadColumn(4)]
        public float Close { get; set; }


        [ColumnName("Volume"), LoadColumn(5)]
        public float Volume { get; set; }


        [ColumnName("Volume Ma"), LoadColumn(6)]
        public float Volume_Ma { get; set; }


        [ColumnName("RSI_50"), LoadColumn(7)]
        public float RSI_50 { get; set; }


        [ColumnName("%K_60"), LoadColumn(8)]
        public float _K_60 { get; set; }


        [ColumnName("%D_1"), LoadColumn(9)]
        public float _D_1 { get; set; }


        [ColumnName("SMA_60"), LoadColumn(10)]
        public float SMA_60 { get; set; }


        [ColumnName("%K_240"), LoadColumn(11)]
        public float _K_240 { get; set; }


        [ColumnName("SMA_240"), LoadColumn(12)]
        public float SMA_240 { get; set; }


        [ColumnName("%K_540"), LoadColumn(13)]
        public float _K_540 { get; set; }


        [ColumnName("SMA_540"), LoadColumn(14)]
        public float SMA_540 { get; set; }


        [ColumnName("%K_1380"), LoadColumn(15)]
        public float _K_1380 { get; set; }


        [ColumnName("SMA_1380"), LoadColumn(16)]
        public float SMA_1380 { get; set; }


        [ColumnName("%K_RSI_15"), LoadColumn(17)]
        public float _K_RSI_15 { get; set; }


        [ColumnName("%D_RSI_1"), LoadColumn(18)]
        public float _D_RSI_1 { get; set; }


        [ColumnName("%K_RSI_30"), LoadColumn(19)]
        public float _K_RSI_30 { get; set; }


        [ColumnName("EMA_100"), LoadColumn(20)]
        public float EMA_100 { get; set; }


        [ColumnName("%K_above"), LoadColumn(21)]
        public float _K_above { get; set; }


        [ColumnName("%K_below"), LoadColumn(22)]
        public float _K_below { get; set; }


        [ColumnName("Within_5%"), LoadColumn(23)]
        public float Within_5_ { get; set; }


        [ColumnName("Price_Above_SMA"), LoadColumn(24)]
        public float Price_Above_SMA { get; set; }


        [ColumnName("Price_Below_SMA"), LoadColumn(25)]
        public float Price_Below_SMA { get; set; }


        [ColumnName("Buy"), LoadColumn(26)]
        public float Buy { get; set; }


        [ColumnName("Sell"), LoadColumn(27)]
        public float Sell { get; set; }


        [ColumnName("Entry_Ind"), LoadColumn(28)]
        public float Entry_Ind { get; set; }


        [ColumnName("Exit_Ind"), LoadColumn(29)]
        public float Exit_Ind { get; set; }


    }
}
