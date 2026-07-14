namespace HighTechTrader
{
    partial class Form1
    {
        private System.ComponentModel.IContainer components = null;

        // ── Ліва колонка — поля вводу ─────────────────────────────────
        private System.Windows.Forms.Label         lblPair;
        private System.Windows.Forms.ComboBox      cmbPair;
        private System.Windows.Forms.Label         lblDirection;
        private System.Windows.Forms.ComboBox      cmbDirection;
        private System.Windows.Forms.Label         lblEntryPrice;
        private System.Windows.Forms.TextBox       txtEntryPrice;
        private System.Windows.Forms.Label         lblStopLoss;
        private System.Windows.Forms.TextBox       txtStopLoss;
        private System.Windows.Forms.Label         lblTakeProfit;
        private System.Windows.Forms.TextBox       txtTakeProfit;
        private System.Windows.Forms.Label         lblRiskPercent;
        private System.Windows.Forms.TextBox       txtRiskPercent;
        private System.Windows.Forms.Label         lblRiskDollar;
        private System.Windows.Forms.TextBox       txtRiskDollar;

        // ── Кнопки ────────────────────────────────────────────────────
        private System.Windows.Forms.Button btnFreqtradeConstructor;
        private System.Windows.Forms.Button btnOpenPosition;
        private System.Windows.Forms.Button btnClosePosition;
        private System.Windows.Forms.Button btnMonitoring;
        private System.Windows.Forms.Button btnLiveOrderBook;

        // ── Центр — баланс ────────────────────────────────────────────
        private System.Windows.Forms.Panel  pnlBalance;
        private System.Windows.Forms.Label  lblBalanceHeader;
        private System.Windows.Forms.Label  lblTotal;
        private System.Windows.Forms.Label  lblAvailable;
        private System.Windows.Forms.Label  lblInPositions;

        // ── Права панель — лог ────────────────────────────────────────
        private System.Windows.Forms.Panel     pnlLog;
        private System.Windows.Forms.Label     lblLogHeader;
        private System.Windows.Forms.RichTextBox rtbLog;
        private System.Windows.Forms.Button    btnClearLog;

        // ── Підвал ────────────────────────────────────────────────────
        private System.Windows.Forms.Label lblFooter;

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            this.SuspendLayout();

            // ── Форма ─────────────────────────────────────────────────
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 16F);
            this.AutoScaleMode       = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor           = System.Drawing.Color.FromArgb(10, 10, 15);
            this.ClientSize          = new System.Drawing.Size(1200, 820);
            this.MinimumSize         = new System.Drawing.Size(1000, 700);
            this.Font                = new System.Drawing.Font("Segoe UI", 9.5F);
            this.ForeColor           = System.Drawing.Color.Cyan;
            this.FormBorderStyle     = System.Windows.Forms.FormBorderStyle.Sizable;
            this.MaximizeBox         = true;
            this.Name                = "Form1";
            this.StartPosition       = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text                = "⚡ High-Tech Trader";

            // ══════════════════════════════════════════════════════════
            // ЛІВА КОЛОНКА (x=30, ширина=380)
            // ══════════════════════════════════════════════════════════

            this.lblPair          = MakeLabel("♦ Пара", 30, 25);
            this.cmbPair          = MakeCombo(30, 50, new string[]{"BTCUSDT","ETHUSDT","SOLUSDT"}, editable: true);
            this.lblDirection     = MakeLabel("♦ Напрямок позиції", 30, 92);
            this.cmbDirection     = MakeCombo(30, 117, new string[]{"Long","Short"}, editable: false);
            this.lblEntryPrice    = MakeLabel("♦ Ціна входу", 30, 159);
            this.txtEntryPrice    = MakeTextBox(30, 184);
            this.lblStopLoss      = MakeLabel("♦ Stop-Loss", 30, 226);
            this.txtStopLoss      = MakeTextBox(30, 251);
            this.lblTakeProfit    = MakeLabel("♦ Тейк-профіт", 30, 293);
            this.txtTakeProfit    = MakeTextBox(30, 318);
            this.lblRiskPercent   = MakeLabel("♦ Ризик % від депозиту", 30, 360);
            this.txtRiskPercent   = MakeTextBox(30, 385, "1.00");
            this.lblRiskDollar    = MakeLabel("♦ Ризик на угоду ($)", 30, 427);
            this.txtRiskDollar    = MakeTextBox(30, 452, "0.20");

            // Кнопки
            this.btnFreqtradeConstructor = MakeButton("🚀 Freqtrade Constructor", 30, 500,
                System.Drawing.Color.FromArgb(0, 51, 102));
            this.btnFreqtradeConstructor.Click +=
                new System.EventHandler(this.btnFreqtradeConstructor_Click);

            this.btnOpenPosition = MakeButton("🟢 Відкрити позицію", 30, 548,
                System.Drawing.Color.FromArgb(0, 80, 0));
            this.btnOpenPosition.Click +=
                new System.EventHandler(this.btnOpenPosition_Click);

            this.btnClosePosition = MakeButton("🔴 Закрити позицію", 30, 596,
                System.Drawing.Color.FromArgb(150, 0, 0));
            this.btnClosePosition.Click +=
                new System.EventHandler(this.btnClosePosition_Click);

            this.btnMonitoring = MakeButton("👋 Моніторинг (3 сек)", 30, 644,
                System.Drawing.Color.FromArgb(20, 80, 20));
            this.btnMonitoring.Click +=
                new System.EventHandler(this.btnMonitoring_Click);

            this.btnLiveOrderBook = MakeButton("📊 LIVE Ордербук", 30, 692,
                System.Drawing.Color.FromArgb(0, 51, 102));
            this.btnLiveOrderBook.Click +=
                new System.EventHandler(this.btnLiveOrderBook_Click);

            // ══════════════════════════════════════════════════════════
            // ЦЕНТР — ПАНЕЛЬ БАЛАНСУ (x=435, ширина=320)
            // ══════════════════════════════════════════════════════════

            this.pnlBalance = new System.Windows.Forms.Panel
            {
                BackColor   = System.Drawing.Color.FromArgb(15, 15, 25),
                BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle,
                Location    = new System.Drawing.Point(435, 25),
                Size        = new System.Drawing.Size(320, 175),
            };

            this.lblBalanceHeader = new System.Windows.Forms.Label
            {
                AutoSize  = true,
                Location  = new System.Drawing.Point(15, 15),
                Text      = "⚠ Активний баланс USDT",
                ForeColor = System.Drawing.Color.FromArgb(255, 215, 0),
                Font      = new System.Drawing.Font("Segoe UI", 10.5F,
                                System.Drawing.FontStyle.Bold),
            };
            this.pnlBalance.Controls.Add(this.lblBalanceHeader);

            this.lblTotal = new System.Windows.Forms.Label
            {
                AutoSize  = true, Location = new System.Drawing.Point(15, 50),
                Text      = "Всього: —",
                ForeColor = System.Drawing.Color.White,
                Font      = new System.Drawing.Font("Segoe UI", 11F,
                                System.Drawing.FontStyle.Bold),
            };
            this.pnlBalance.Controls.Add(this.lblTotal);

            this.lblAvailable = new System.Windows.Forms.Label
            {
                AutoSize  = true, Location = new System.Drawing.Point(15, 85),
                Text      = "Доступно: —",
                ForeColor = System.Drawing.Color.FromArgb(0, 220, 180),
                Font      = new System.Drawing.Font("Segoe UI", 10.5F),
            };
            this.pnlBalance.Controls.Add(this.lblAvailable);

            this.lblInPositions = new System.Windows.Forms.Label
            {
                AutoSize  = true, Location = new System.Drawing.Point(15, 118),
                Text      = "У позиціях: —",
                ForeColor = System.Drawing.Color.FromArgb(255, 100, 100),
                Font      = new System.Drawing.Font("Segoe UI", 10.5F),
            };
            this.pnlBalance.Controls.Add(this.lblInPositions);

            // ══════════════════════════════════════════════════════════
            // ПРАВА ПАНЕЛЬ — ЛОГ (x=770, ширина=410)
            // ══════════════════════════════════════════════════════════

            this.pnlLog = new System.Windows.Forms.Panel
            {
                BackColor   = System.Drawing.Color.FromArgb(8, 8, 18),
                BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle,
                Location    = new System.Drawing.Point(770, 25),
                Size        = new System.Drawing.Size(410, 755),
                Anchor      = System.Windows.Forms.AnchorStyles.Top
                            | System.Windows.Forms.AnchorStyles.Bottom
                            | System.Windows.Forms.AnchorStyles.Right,
            };

            // Заголовок панелі логу
            this.lblLogHeader = new System.Windows.Forms.Label
            {
                Text      = "📋  Лог подій",
                Location  = new System.Drawing.Point(10, 10),
                Size      = new System.Drawing.Size(300, 26),
                ForeColor = System.Drawing.Color.FromArgb(255, 215, 0),
                Font      = new System.Drawing.Font("Segoe UI", 11F,
                                System.Drawing.FontStyle.Bold),
            };
            this.pnlLog.Controls.Add(this.lblLogHeader);

            // Кнопка очистити лог
            this.btnClearLog = new System.Windows.Forms.Button
            {
                Text      = "🗑",
                Location  = new System.Drawing.Point(360, 8),
                Size      = new System.Drawing.Size(36, 28),
                BackColor = System.Drawing.Color.FromArgb(60, 20, 20),
                ForeColor = System.Drawing.Color.White,
                FlatStyle = System.Windows.Forms.FlatStyle.Flat,
                Font      = new System.Drawing.Font("Segoe UI", 10F),
            };
            this.btnClearLog.FlatAppearance.BorderSize = 0;
            this.btnClearLog.Click += (s, e) => rtbLog.Clear();
            this.pnlLog.Controls.Add(this.btnClearLog);

            // RichTextBox для логу
            this.rtbLog = new System.Windows.Forms.RichTextBox
            {
                Location    = new System.Drawing.Point(10, 44),
                Size        = new System.Drawing.Size(388, 700),
                Anchor      = System.Windows.Forms.AnchorStyles.Top
                            | System.Windows.Forms.AnchorStyles.Bottom
                            | System.Windows.Forms.AnchorStyles.Left
                            | System.Windows.Forms.AnchorStyles.Right,
                BackColor   = System.Drawing.Color.FromArgb(8, 8, 18),
                ForeColor   = System.Drawing.Color.FromArgb(0, 220, 180),
                Font        = new System.Drawing.Font("Consolas", 9.5F),
                ReadOnly    = true,
                BorderStyle = System.Windows.Forms.BorderStyle.None,
                ScrollBars  = System.Windows.Forms.RichTextBoxScrollBars.Vertical,
                WordWrap    = true,
            };
            this.pnlLog.Controls.Add(this.rtbLog);

            // ══════════════════════════════════════════════════════════
            // ПІДВАЛ
            // ══════════════════════════════════════════════════════════

            this.lblFooter = new System.Windows.Forms.Label
            {
                AutoSize  = true,
                Location  = new System.Drawing.Point(30, 790),
                Text      = "High-Tech Trader • WebSocket Ордербук + Баланс у реальному часі",
                ForeColor = System.Drawing.Color.FromArgb(80, 80, 100),
                Font      = new System.Drawing.Font("Segoe UI", 9F),
                Anchor    = System.Windows.Forms.AnchorStyles.Bottom
                          | System.Windows.Forms.AnchorStyles.Left,
            };

            // ── Додаємо все на форму ──────────────────────────────────
            this.Controls.AddRange(new System.Windows.Forms.Control[]
            {
                this.lblPair, this.cmbPair,
                this.lblDirection, this.cmbDirection,
                this.lblEntryPrice, this.txtEntryPrice,
                this.lblStopLoss, this.txtStopLoss,
                this.lblTakeProfit, this.txtTakeProfit,
                this.lblRiskPercent, this.txtRiskPercent,
                this.lblRiskDollar, this.txtRiskDollar,
                this.btnFreqtradeConstructor,
                this.btnOpenPosition,
                this.btnClosePosition,
                this.btnMonitoring,
                this.btnLiveOrderBook,
                this.pnlBalance,
                this.pnlLog,
                this.lblFooter,
            });

            this.ResumeLayout(false);
            this.PerformLayout();
        }

        // ── Хелпери для коротшого запису ──────────────────────────────

        private System.Windows.Forms.Label MakeLabel(string text, int x, int y)
        {
            return new System.Windows.Forms.Label
            {
                AutoSize  = true,
                Location  = new System.Drawing.Point(x, y),
                Text      = text,
                ForeColor = System.Drawing.Color.Cyan,
                Font      = new System.Drawing.Font("Segoe UI", 10.5F),
            };
        }

        private System.Windows.Forms.TextBox MakeTextBox(int x, int y, string text = "")
        {
            return new System.Windows.Forms.TextBox
            {
                Location    = new System.Drawing.Point(x, y),
                Size        = new System.Drawing.Size(380, 32),
                Text        = text,
                BackColor   = System.Drawing.Color.FromArgb(20, 20, 30),
                ForeColor   = System.Drawing.Color.White,
                BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle,
                Font        = new System.Drawing.Font("Segoe UI", 10F),
            };
        }

        private System.Windows.Forms.ComboBox MakeCombo(int x, int y,
            string[] items, bool editable)
        {
            var cb = new System.Windows.Forms.ComboBox
            {
                Location      = new System.Drawing.Point(x, y),
                Size          = new System.Drawing.Size(380, 32),
                DropDownStyle = editable
                    ? System.Windows.Forms.ComboBoxStyle.DropDown
                    : System.Windows.Forms.ComboBoxStyle.DropDownList,
                BackColor     = System.Drawing.Color.FromArgb(20, 20, 30),
                ForeColor     = System.Drawing.Color.Cyan,
                FlatStyle     = System.Windows.Forms.FlatStyle.Flat,
                Font          = new System.Drawing.Font("Segoe UI", 10F),
            };
            cb.Items.AddRange(items);
            if (items.Length > 0) cb.SelectedIndex = 0;
            return cb;
        }

        private System.Windows.Forms.Button MakeButton(string text, int x, int y,
            System.Drawing.Color color)
        {
            var btn = new System.Windows.Forms.Button
            {
                Text      = text,
                Location  = new System.Drawing.Point(x, y),
                Size      = new System.Drawing.Size(380, 42),
                BackColor = color,
                ForeColor = System.Drawing.Color.White,
                FlatStyle = System.Windows.Forms.FlatStyle.Flat,
                Font      = new System.Drawing.Font("Segoe UI", 11F,
                                System.Drawing.FontStyle.Bold),
            };
            btn.FlatAppearance.BorderSize = 0;
            return btn;
        }

        #endregion

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }
    }
}