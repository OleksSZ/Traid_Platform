using System;
using System.IO;
using System.Windows.Forms;

namespace HighTechTrader
{
    /// <summary>
    /// Моніторинг балансу та позицій через cs_bridge.py.
    /// </summary>
    public class MonitorService : PythonRunnerBase, IMonitor
    {
        public event BalanceUpdatedHandler OnBalanceUpdated;

        private readonly System.Windows.Forms.Timer _balanceTimer;
        private readonly System.Windows.Forms.Timer _monitorTimer;
        private readonly string _bridge;

        public bool IsMonitoring => _monitorTimer.Enabled;

        public MonitorService(string pythonExe, string scriptsFolder)
            : base(pythonExe, scriptsFolder)
        {
            _bridge = Path.Combine(scriptsFolder, "cs_bridge.py");

            // Баланс кожні 10 сек
            _balanceTimer = new System.Windows.Forms.Timer { Interval = 10000 };
            _balanceTimer.Tick += (_, __) => RefreshBalance();
            _balanceTimer.Start();

            // Монітор позицій — запускається вручну
            _monitorTimer = new System.Windows.Forms.Timer { Interval = 3000 };
            _monitorTimer.Tick += (_, __) => RefreshPositions();
        }

        public void StartMonitoring(int intervalMs = 3000)
        {
            _monitorTimer.Interval = intervalMs;
            _monitorTimer.Start();
            Log("✅ Моніторинг запущено");
        }

        public void StopMonitoring()
        {
            _monitorTimer.Stop();
            Log("⏹ Моніторинг зупинено");
        }

        public BalanceInfo GetBalance()
        {
            if (!File.Exists(_bridge))
            {
                Log($"❌ cs_bridge.py не знайдено: {_bridge}");
                return null;
            }

            string output = RunScript(_bridge, "get_balance \"{}\"");
            return ParseBridgeBalance(output);
        }

        // ── Приватні ──────────────────────────────────────────────────

        private void RefreshBalance()
        {
            var bal = GetBalance();
            if (bal != null)
                OnBalanceUpdated?.Invoke(bal);
        }

        private void RefreshPositions()
        {
            if (!File.Exists(_bridge)) return;
            string output = RunScript(_bridge, "monitor \"{}\"");
            if (!string.IsNullOrWhiteSpace(output))
                Log($"[Monitor] {ExtractInfo(output)}");
        }

        private BalanceInfo ParseBridgeBalance(string output)
        {
            if (string.IsNullOrWhiteSpace(output)) return null;
            try
            {
                string lastLine = output.Trim().Split('\n')[^1].Trim();
                dynamic result  = Newtonsoft.Json.JsonConvert.DeserializeObject(lastLine);

                if (!(bool)result.ok) return null;

                return new BalanceInfo
                {
                    Total       = (decimal)(double)result.data.total,
                    Available   = (decimal)(double)result.data.available,
                    InPositions = (decimal)(double)result.data.used
                };
            }
            catch (Exception ex)
            {
                Log($"⚠️ Баланс: {ex.Message}");
                return null;
            }
        }

        private string ExtractInfo(string output)
        {
            try
            {
                string lastLine = output.Trim().Split('\n')[^1].Trim();
                dynamic result  = Newtonsoft.Json.JsonConvert.DeserializeObject(lastLine);
                return result.data?.info?.ToString() ?? "—";
            }
            catch { return output; }
        }

        public void Dispose()
        {
            _balanceTimer?.Stop();
            _balanceTimer?.Dispose();
            _monitorTimer?.Stop();
            _monitorTimer?.Dispose();
        }
    }
}