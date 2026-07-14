using System;

namespace HighTechTrader
{
    //Делегати
    public delegate void LogEventHandler(string message);
    public delegate void BalanceUpdatedHandler(BalanceInfo balance);
    public delegate void TradeOpenedHandler(TradeInfo trade);
    public delegate void TradeClosedHandler(string pair, string reason);

    //Моделі 
    public class BalanceInfo
    {
        public decimal Total       { get; set; }
        public decimal Available   { get; set; }
        public decimal InPositions { get; set; }
    }

    public class TradeInfo
    {
        public string  Pair            { get; set; }
        public string  Direction       { get; set; }
        public decimal EntryPrice      { get; set; }
        public decimal StopLoss        { get; set; }
        public decimal TakeProfit      { get; set; }
        public decimal RiskPercent     { get; set; }
        public decimal RiskDollar      { get; set; }
        public int     Leverage        { get; set; }
        public double  RR              { get; set; }
        public string  ReasonEntry     { get; set; }
        public int     FearGreed       { get; set; }
        public int     ProfitChance    { get; set; }
        public string  TradingViewLink { get; set; }
    }

    //Інтерфейси
    public interface ITrader
    {
        event LogEventHandler    OnLog;
        event TradeOpenedHandler OnTradeOpened;
        event TradeClosedHandler OnTradeClosed;

        (bool success, string message) OpenTrade(TradeInfo trade);
        (bool success, string message) CloseTrade(string pair, string reason);
        string[] GetOpenPositions();
        string   MonitorTrades();
    }

    public interface IMonitor
    {
        event LogEventHandler       OnLog;
        event BalanceUpdatedHandler OnBalanceUpdated;

        void        StartMonitoring(int intervalMs);
        void        StopMonitoring();
        bool        IsMonitoring { get; }
        BalanceInfo GetBalance();
    }

    public interface IPythonRunner
    {
        event LogEventHandler OnLog;

        string RunScript(string scriptPath, string arguments = "");
        void   RunScriptAsync(string scriptPath, string arguments = "");
        bool   IsPythonAvailable();
    }
}