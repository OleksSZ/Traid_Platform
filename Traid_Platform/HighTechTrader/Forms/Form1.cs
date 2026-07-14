using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace HighTechTrader
{
    public partial class Form1 : Form
    {
        // Конфігурація — де шукти .py файли
        private const string PYTHON_EXE       = @"python.exe";
        // .py файли лежать в Traid_Platform\ (батьківська папка HighTechTrader)
        // AppBase = bin\Debug\net10.0-windows\ → 4 рівні вгору = Traid_Platform\
        private static readonly string SCRIPTS_FOLDER =
            Path.GetFullPath(Path.Combine(
                AppDomain.CurrentDomain.BaseDirectory, @"..\..\..\..\")); 
        private const string FREQTRADE_FOLDER = @"D:\Trading\freqtrade";

        private TraderService    _trader;
        private MonitorService   _monitor;
        private FreqtradeService _freqtrade;

        public Form1()
        {
            InitializeComponent();
            InitServices();
            BindEvents();
            LoadPairs();
            Log("✅ High-Tech Trader запущено", Color.FromArgb(0, 255, 170));
            Log($"📁 Scripts: {SCRIPTS_FOLDER}", Color.Gray);
            Log($"🐍 Python:  {PYTHON_EXE}", Color.Gray);
            _monitor.GetBalance();
        }

        //  Сервіси
        private void InitServices()
        {
            _trader    = new TraderService(PYTHON_EXE, SCRIPTS_FOLDER);
            _monitor   = new MonitorService(PYTHON_EXE, SCRIPTS_FOLDER);
            _freqtrade = new FreqtradeService(FREQTRADE_FOLDER);
        }

        private void BindEvents()
        {
            _trader.OnLog    += msg => Log(msg, Color.FromArgb(0, 220, 180));
            _monitor.OnLog   += msg => Log(msg, Color.Gray);
            _freqtrade.OnLog += msg => Log(msg, Color.FromArgb(100, 180, 255));

            _monitor.OnBalanceUpdated += OnBalanceUpdated;

            _trader.OnTradeOpened += trade =>
                Log($"🟢 Відкрито: {trade.Pair} {trade.Direction} | RR {trade.RR:F2}",
                    Color.FromArgb(0, 255, 100));

            _trader.OnTradeClosed += (pair, reason) =>
                Log($"🔴 Закрито: {pair} | {reason}",
                    Color.FromArgb(255, 80, 80));
        }

        // Завантаження пар 
        private void LoadPairs()
        {
            string pairsFile = Path.Combine(SCRIPTS_FOLDER, "active_pairs.txt");
            string[] pairs = { "BTCUSDT", "ETHUSDT", "SOLUSDT", "CAKEUSDT", "XRPUSDT" };

            if (File.Exists(pairsFile))
            {
                try
                {
                    string content = File.ReadAllText(pairsFile).Trim();
                    if (!string.IsNullOrEmpty(content))
                        pairs = content.Split(new[] { ',' },
                            StringSplitOptions.RemoveEmptyEntries);
                }
                catch (Exception ex)
                {
                    Log($"⚠️ Пари: {ex.Message}", Color.Orange);
                }
            }

            cmbPair.Items.Clear();
            foreach (var p in pairs)
                cmbPair.Items.Add(p.Trim().ToUpper());
            cmbPair.Text = "BTCUSDT";
            Log($"✅ Пар завантажено: {pairs.Length}", Color.Gray);
        }

        // ══════════════════════════════════════════════════════════════
        // КНОПКИ


        private void btnFreqtradeConstructor_Click(object sender, EventArgs e)
        {
            Log("🚀 Запуск Freqtrade...", Color.FromArgb(100, 180, 255));
            try
            {
                _freqtrade.Launch();
            }
            catch (Exception ex)
            {
                Log($"❌ Freqtrade: {ex.Message}", Color.Red);
            }
        }

        private void btnOpenPosition_Click(object sender, EventArgs e)
        {
            Log("─────────────────────────────", Color.FromArgb(40, 40, 60));
            Log("🔄 Відкриття позиції...", Color.Cyan);

            if (!TryReadInputs(out TradeInfo trade))
                return;

            Log($"→ Пара:      {trade.Pair}", Color.White);
            Log($"→ Напрямок:  {trade.Direction}", Color.White);
            Log($"→ Вхід:      {trade.EntryPrice}", Color.White);
            Log($"→ Stop-Loss: {trade.StopLoss}", Color.White);
            Log($"→ Take:      {trade.TakeProfit}", Color.White);
            Log($"→ Ризик:     {trade.RiskPercent}% / ${trade.RiskDollar}", Color.White);

            try
            {
                using var dlg = new OpenTradeDialog(trade);
                dlg.ValidateDelegate = t =>
                {
                    bool ok = t.RR >= 1.5;
                    return (ok, $"RR {t.RR:F2} < 1.5 — занадто низький");
                };

                if (dlg.ShowDialog() == DialogResult.OK)
                {
                    Log("→ Діалог підтверджено", Color.Gray);
                    var (success, msg) = _trader.OpenTrade(dlg.ResultTrade);
                    Log(success ? $"✅ {msg}" : $"❌ {msg}",
                        success ? Color.FromArgb(0, 255, 100) : Color.Red);
                }
                else
                {
                    Log("⏹ Скасовано користувачем", Color.Gray);
                }
            }
            catch (Exception ex)
            {
                Log($"❌ Виняток: {ex.Message}", Color.Red);
                Log(ex.StackTrace, Color.FromArgb(150, 50, 50));
            }
        }

        private void btnClosePosition_Click(object sender, EventArgs e)
        {
            Log("─────────────────────────────", Color.FromArgb(40, 40, 60));
            Log("🔄 Закриття позиції...", Color.Cyan);

            try
            {
                string[] positions = _trader.GetOpenPositions();
                Log($"→ Знайдено позицій: {positions.Length}", Color.Gray);

                if (positions.Length == 0)
                {
                    Log("ℹ️ Немає відкритих позицій", Color.Orange);
                    MessageBox.Show("Немає відкритих позицій.", "Інфо",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }

                using var dlg = new CloseTradeDialog(positions);
                if (dlg.ShowDialog() == DialogResult.OK)
                {
                    Log($"→ Закриваємо: {dlg.SelectedPair}", Color.White);
                    var (success, msg) = _trader.CloseTrade(dlg.SelectedPair, dlg.CloseReason);
                    Log(success ? $"✅ {msg}" : $"❌ {msg}",
                        success ? Color.FromArgb(0, 255, 100) : Color.Red);
                }
                else
                {
                    Log("⏹ Скасовано", Color.Gray);
                }
            }
            catch (Exception ex)
            {
                Log($"❌ Виняток: {ex.Message}", Color.Red);
            }
        }

        private void btnMonitoring_Click(object sender, EventArgs e)
        {
            if (_monitor.IsMonitoring)
            {
                _monitor.StopMonitoring();
                btnMonitoring.Text = "👋 Моніторинг (В реальному часі)";
                Log("⏹ Моніторинг зупинено", Color.Orange);
            }
            else
            {
                _monitor.StartMonitoring(3000);
                btnMonitoring.Text = "⏹ Зупинити моніторинг";
                Log("✅ Моніторинг запущено (В реальному часі)", Color.FromArgb(0, 255, 100));
            }
        }

        private void btnLiveOrderBook_Click(object sender, EventArgs e)
        {
            string pair   = cmbPair.Text.Trim().ToUpper();
            string script = Path.Combine(SCRIPTS_FOLDER, "orderbook_window.py");
            Log($"📊 Order Book: {pair}", Color.FromArgb(100, 180, 255));

            if (!File.Exists(script))
            {
                Log($"❌ Скрипт не знайдено: {script}", Color.Red);
                return;
            }
            _trader.RunScriptAsync(script, $"--pair {pair}");
        }

        // ══════════════════════════════════════════════════════════════
        // БАЛАНС та ЛОГ
        // ══════════════════════════════════════════════════════════════

        private void OnBalanceUpdated(BalanceInfo bal)
        {
            if (InvokeRequired)
            {
                Invoke(new Action(() => OnBalanceUpdated(bal)));
                return;
            }
            lblTotal.Text       = $"Всього: ${bal.Total:F2}";
            lblAvailable.Text   = $"Доступно: ${bal.Available:F2}";
            lblInPositions.Text = $"У позиціях: ${bal.InPositions:F2}";
        }

        /// <summary>
        /// Основний метод логування — пише в RichTextBox справа і в термінал
        /// </summary>
        private void Log(string message, Color color)
        {
            if (string.IsNullOrEmpty(message)) return;

            // Потокобезпека
            if (InvokeRequired)
            {
                Invoke(new Action(() => Log(message, color)));
                return;
            }

            // 1) Термінал (для дебагу)
            Console.WriteLine(message);

            // 2) RichTextBox справа — з кольором і часом
            string line = $"[{DateTime.Now:HH:mm:ss}] {message}";
            rtbLog.SelectionStart  = rtbLog.TextLength;
            rtbLog.SelectionLength = 0;
            rtbLog.SelectionColor  = color;
            rtbLog.AppendText(line + Environment.NewLine);
            rtbLog.SelectionColor  = rtbLog.ForeColor;

            // Автоскрол вниз
            rtbLog.ScrollToCaret();

            // 3) Підвал — остання подія
            lblFooter.Text = message;
        }

        // ── Перевантаження без кольору (для зворотної сумісності) ─────
        private void AppendLog(string message)
            => Log(message, Color.FromArgb(0, 220, 180));

        // ── Читання полів форми ───────────────────────────────────────
        private bool TryReadInputs(out TradeInfo trade)
        {
            trade = new TradeInfo();
            try
            {
                trade.Pair        = cmbPair.Text.Trim().ToUpper();
                trade.Direction   = cmbDirection.Text.ToLower();
                trade.EntryPrice  = ParseDecimal(txtEntryPrice.Text);
                trade.StopLoss    = ParseDecimal(txtStopLoss.Text);
                trade.TakeProfit  = ParseDecimal(txtTakeProfit.Text);
                trade.RiskPercent = ParseDecimal(txtRiskPercent.Text);
                trade.RiskDollar  = ParseDecimal(txtRiskDollar.Text);

                if (string.IsNullOrWhiteSpace(trade.Pair))
                    throw new Exception("Пара не вказана");
                if (trade.EntryPrice <= 0)
                    throw new Exception("Ціна входу має бути > 0");
                if (trade.StopLoss <= 0)
                    throw new Exception("Stop-Loss має бути > 0");
                if (trade.TakeProfit <= 0)
                    throw new Exception("Take-Profit має бути > 0");

                return true;
            }
            catch (Exception ex)
            {
                Log($"❌ Помилка вводу: {ex.Message}", Color.Red);
                MessageBox.Show($"Перевірте поля!\n\n{ex.Message}",
                    "Помилка вводу", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
        }

        private decimal ParseDecimal(string s)
            => decimal.Parse(s.Trim().Replace(",", "."),
                System.Globalization.CultureInfo.InvariantCulture);

        // ── Закриття ──────────────────────────────────────────────────
        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            Log("👋 Завершення роботи...", Color.Gray);
            _monitor?.StopMonitoring();
            _monitor?.Dispose();
            base.OnFormClosing(e);
        }
    }
}