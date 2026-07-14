using System;
using System.IO;

namespace HighTechTrader
{
    /// <summary>
    /// Викликає cs_bridge.py для всіх торгових операцій.
    /// Успадковує PythonRunnerBase (RunScript, Log).
    /// </summary>
    public class TraderService : PythonRunnerBase, ITrader
    {
        public event TradeOpenedHandler OnTradeOpened;
        public event TradeClosedHandler OnTradeClosed;

        private readonly string _bridge;

        public TraderService(string pythonExe, string scriptsFolder)
            : base(pythonExe, scriptsFolder)
        {
            _bridge = Path.Combine(scriptsFolder, "cs_bridge.py");
        }

        // ── ITrader ────────────────────────────────────────────────────

        public (bool success, string message) OpenTrade(TradeInfo trade)
        {
            // 1. Локальна перевірка RR перед викликом Python
            var (rrOk, rrMsg) = CheckRR(trade);
            if (!rrOk)
            {
                Log($"⚠️ RR: {rrMsg}");
                return (false, rrMsg);
            }

            // 2. Рахуємо плече через cs_bridge
            int leverage = CalcLeverage(trade);
            if (leverage < 1) leverage = 1;
            trade.Leverage = leverage;
            Log($"→ Плече: {leverage}x");

            // 3. Відкриваємо позицію
            string json = BuildJson(new {
                pair        = trade.Pair,
                direction   = trade.Direction,
                entry       = trade.EntryPrice,
                stop        = trade.StopLoss,
                take        = trade.TakeProfit,
                leverage    = leverage,
                risk_dollar = trade.RiskDollar,
                risk_percent= trade.RiskPercent,
                reason      = trade.ReasonEntry,
                fear_greed  = trade.FearGreed
            });

            var (ok, data, error) = CallBridge("open_trade", json);
            string msg = ok
                ? data?["message"]?.ToString() ?? "✅ Відкрито"
                : $"❌ {error}";

            Log(msg);
            if (ok) OnTradeOpened?.Invoke(trade);
            return (ok, msg);
        }

        public (bool success, string message) CloseTrade(string pair, string reason)
        {
            string json = BuildJson(new { pair, reason });
            var (ok, data, error) = CallBridge("close_trade", json);
            string msg = ok
                ? data?["message"]?.ToString() ?? "✅ Закрито"
                : $"❌ {error}";

            Log(msg);
            if (ok) OnTradeClosed?.Invoke(pair, reason);
            return (ok, msg);
        }

        public string[] GetOpenPositions()
        {
            var (ok, data, error) = CallBridge("get_positions", "{}");
            if (!ok || data == null)
            {
                Log($"⚠️ get_positions: {error}");
                return Array.Empty<string>();
            }

            // data["positions"] = ["BTCUSDT (LONG)", ...]
            var arr = data["positions"] as Newtonsoft.Json.Linq.JArray
                      ?? new Newtonsoft.Json.Linq.JArray();
            var result = new string[arr.Count];
            for (int i = 0; i < arr.Count; i++)
                result[i] = arr[i].ToString();
            return result;
        }

        public string MonitorTrades()
        {
            var (ok, data, error) = CallBridge("monitor", "{}");
            if (!ok) return $"❌ {error}";
            return data?["info"]?.ToString() ?? "Немає активних позицій.";
        }

        // ── Приватні хелпери ───────────────────────────────────────────

        private int CalcLeverage(TradeInfo trade)
        {
            string json = BuildJson(new {
                entry      = trade.EntryPrice,
                stop       = trade.StopLoss,
                risk_usd   = trade.RiskDollar,
                risk_percent = trade.RiskPercent
            });

            var (ok, data, error) = CallBridge("calc_leverage", json);
            if (ok && data != null && data["leverage"] != null)
            {
                if (int.TryParse(data["leverage"].ToString(), out int lev))
                    return lev;
            }
            Log($"⚠️ Плече fallback: {error}");
            return FallbackLeverage(trade);
        }

        private int FallbackLeverage(TradeInfo trade)
        {
            double stopPct = Math.Abs((double)(trade.EntryPrice - trade.StopLoss)
                             / (double)trade.EntryPrice);
            if (stopPct <= 0) return 1;
            int lev = (int)Math.Floor((double)trade.RiskPercent / 100.0 / stopPct);
            return Math.Max(1, Math.Min(lev, 125));
        }

        private (bool ok, string message) CheckRR(TradeInfo t)
        {
            double entry  = (double)t.EntryPrice;
            double stop   = (double)t.StopLoss;
            double take   = (double)t.TakeProfit;
            bool   isLong = t.Direction.ToLower() == "long";

            if (isLong && stop >= entry)
                return (false, "Long: Stop-Loss має бути нижче ціни входу");
            if (isLong && take <= entry)
                return (false, "Long: Take-Profit має бути вище ціни входу");
            if (!isLong && stop <= entry)
                return (false, "Short: Stop-Loss має бути вище ціни входу");
            if (!isLong && take >= entry)
                return (false, "Short: Take-Profit має бути нижче ціни входу");

            double risk   = isLong ? entry - stop  : stop - entry;
            double reward = isLong ? take  - entry : entry - take;
            double rr     = reward / risk;
            t.RR = Math.Round(rr, 4);

            if (rr < 2.0)
                return (false, $"RR {rr:F2} < 2.0 — мінімум 1:2");

            return (true, $"RR {rr:F2} ✅");
        }

        // Bridge виклик

        /// <summary>
        /// Викликає cs_bridge.py і парсить JSON відповідь.
        /// Повертає (ok, data_object, error_string).
        /// </summary>
        private (bool ok, dynamic data, string error) CallBridge(
            string action, string jsonArgs)
        {
            if (!File.Exists(_bridge))
            {
                string err = $"cs_bridge.py не знайдено: {_bridge}";
                Log($"❌ {err}");
                return (false, null, err);
            }

            // Екрануємо JSON для передачі як аргумент командного рядка
            string safeJson = jsonArgs.Replace("\"", "\\\"");
            string output   = RunScript(_bridge, $"{action} \"{safeJson}\"");

            if (string.IsNullOrWhiteSpace(output))
                return (false, null, "Python не повернув відповідь");

            try
            {
                // Беремо останній рядок (Python може виводити warnings перед JSON)
                string lastLine = output.Trim().Split('\n')[^1].Trim();
                dynamic result  = Newtonsoft.Json.JsonConvert.DeserializeObject(lastLine);

                bool   ok    = (bool)result.ok;
                string error = result.error?.ToString() ?? "";
                return (ok, result.data, error);
            }
            catch (Exception ex)
            {
                Log($"⚠️ Парсинг відповіді: {ex.Message}\nВихід: {output}");
                return (false, null, $"Помилка парсингу: {output}");
            }
        }

        //JSON builder без Newtonsoft

        private string BuildJson(object obj)
        {
            // Використовуємо Newtonsoft якщо є, інакше вручну
            try
            {
                return Newtonsoft.Json.JsonConvert.SerializeObject(obj);
            }
            catch
            {
                return "{}";
            }
        }
    }
}