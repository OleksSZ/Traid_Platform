using System;
using System.ComponentModel;
using System.Drawing;
using System.Windows.Forms;

namespace HighTechTrader
{
    public class OpenTradeDialog : Form
    {
        private TradeInfo _trade;
        public  TradeInfo ResultTrade => _trade;

        private Label         lblTitle;
        private Label         lblRR;
        private Label         lblWarning;
        private TextBox       txtReason;
        private NumericUpDown nudFearGreed;
        private NumericUpDown nudProfitChance;
        private TextBox       txtTVLink;
        private Button        btnOK;
        private Button        btnCancel;

        [DesignerSerializationVisibility(DesignerSerializationVisibility.Hidden)]
        public Func<TradeInfo, (bool ok, string msg)> ValidateDelegate { get; set; }

        public OpenTradeDialog(TradeInfo trade)
        {
            _trade = trade ?? throw new ArgumentNullException(nameof(trade));
            CalculateRR();
            InitializeComponent();
            PopulateInfo();
        }

        private void CalculateRR()
        {
            double entry  = (double)_trade.EntryPrice;
            double stop   = (double)_trade.StopLoss;
            double take   = (double)_trade.TakeProfit;
            double risk   = _trade.Direction.ToLower() == "long" ? entry - stop : stop - entry;
            double reward = _trade.Direction.ToLower() == "long" ? take - entry : entry - take;
            _trade.RR = risk > 0 ? Math.Round(reward / risk, 4) : 0;
        }

        private void PopulateInfo()
        {
            lblTitle.Text = $"Відкриття {_trade.Pair} — {_trade.Direction.ToUpper()}";

            bool   rrOk     = _trade.RR >= 1.5;
            double potProfit = (double)_trade.RiskDollar * _trade.RR;
            double potLoss   = -(double)_trade.RiskDollar;

            lblRR.Text      = $"RR: {_trade.RR:F2}   Прибуток: +${potProfit:F2}   Збиток: ${potLoss:F2}";
            lblRR.ForeColor = rrOk ? Color.FromArgb(0, 255, 170) : Color.FromArgb(255, 68, 68);

            if (!rrOk)
            {
                lblWarning.Visible = true;
                lblWarning.Text    = $"⚠️ RR {_trade.RR:F2} < 1.5 — занадто низький!";
                btnOK.Enabled      = false;
            }
        }

        private void btnOK_Click(object sender, EventArgs e)
        {
            if (ValidateDelegate != null)
            {
                var (ok, msg) = ValidateDelegate(_trade);
                if (!ok)
                {
                    MessageBox.Show(msg, "Помилка RR", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
            }

            _trade.ReasonEntry     = txtReason.Text.Trim();
            _trade.FearGreed       = (int)nudFearGreed.Value;
            _trade.ProfitChance    = (int)nudProfitChance.Value;
            _trade.TradingViewLink = txtTVLink.Text.Trim();

            DialogResult = DialogResult.OK;
            Close();
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            DialogResult = DialogResult.Cancel;
            Close();
        }

        private void InitializeComponent()
        {
            this.SuspendLayout();

            this.Text            = "🟢 Відкриття позиції";
            this.BackColor       = Color.FromArgb(10, 10, 15);
            this.ForeColor       = Color.FromArgb(0, 255, 170);
            this.Font            = new Font("Segoe UI", 10F);
            this.ClientSize      = new Size(620, 540);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox     = false;
            this.StartPosition   = FormStartPosition.CenterParent;

            int y = 20;

            lblTitle = AddLabel("", 20, y, 580, 30, 14F, bold: true, color: Color.FromArgb(0, 255, 170));
            y += 44;

            lblRR = AddLabel("", 20, y, 580, 24, 10F);
            y += 36;

            lblWarning = AddLabel("", 20, y, 580, 24, 10F, color: Color.FromArgb(255, 68, 68));
            lblWarning.Visible = false;
            y += 30;

            y = AddInfoRow("Пара",        _trade.Pair,                y);
            y = AddInfoRow("Напрямок",    _trade.Direction.ToUpper(), y);
            y = AddInfoRow("Ціна входу",  $"{_trade.EntryPrice:F4}",  y);
            y = AddInfoRow("Stop-Loss",   $"{_trade.StopLoss:F4}",    y);
            y = AddInfoRow("Take-Profit", $"{_trade.TakeProfit:F4}",  y);
            y = AddInfoRow("Ризик $",     $"${_trade.RiskDollar:F2}", y);
            y += 10;

            AddLabel("Причина входу:", 20, y, 200, 22, 10F);
            y += 24;
            txtReason = new TextBox
            {
                Multiline       = true,
                Height          = 60,
                Location        = new Point(20, y),
                Size            = new Size(580, 60),
                BackColor       = Color.FromArgb(20, 20, 30),
                ForeColor       = Color.White,
                BorderStyle     = BorderStyle.FixedSingle,
                PlaceholderText = "Чому відкриваємо позицію?"
            };
            Controls.Add(txtReason);
            y += 70;

            AddLabel("Fear & Greed:", 20, y, 160, 22, 10F);
            nudFearGreed = new NumericUpDown
            {
                Minimum   = 0, Maximum = 100, Value = 50,
                Location  = new Point(170, y),
                Size      = new Size(80, 26),
                BackColor = Color.FromArgb(20, 20, 30),
                ForeColor = Color.White
            };
            Controls.Add(nudFearGreed);

            AddLabel("Шанс профіту (%):", 280, y, 180, 22, 10F);
            nudProfitChance = new NumericUpDown
            {
                Minimum   = 0, Maximum = 100, Value = 65,
                Location  = new Point(460, y),
                Size      = new Size(80, 26),
                BackColor = Color.FromArgb(20, 20, 30),
                ForeColor = Color.White
            };
            Controls.Add(nudProfitChance);
            y += 40;

            AddLabel("TradingView посилання:", 20, y, 220, 22, 10F);
            y += 24;
            txtTVLink = new TextBox
            {
                Location        = new Point(20, y),
                Size            = new Size(580, 26),
                BackColor       = Color.FromArgb(20, 20, 30),
                ForeColor       = Color.White,
                BorderStyle     = BorderStyle.FixedSingle,
                PlaceholderText = "https://www.tradingview.com/chart/..."
            };
            Controls.Add(txtTVLink);
            y += 44;

            btnOK = new Button
            {
                Text      = "✅ Підтвердити",
                Location  = new Point(20, y),
                Size      = new Size(280, 42),
                BackColor = Color.FromArgb(0, 100, 0),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font      = new Font("Segoe UI", 11F, FontStyle.Bold)
            };
            btnOK.FlatAppearance.BorderSize = 0;
            btnOK.Click += btnOK_Click;
            Controls.Add(btnOK);

            btnCancel = new Button
            {
                Text      = "❌ Скасувати",
                Location  = new Point(320, y),
                Size      = new Size(280, 42),
                BackColor = Color.FromArgb(150, 0, 0),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font      = new Font("Segoe UI", 11F, FontStyle.Bold)
            };
            btnCancel.FlatAppearance.BorderSize = 0;
            btnCancel.Click += btnCancel_Click;
            Controls.Add(btnCancel);

            this.ClientSize = new Size(620, y + 62);
            this.ResumeLayout(false);
        }

        private Label AddLabel(string text, int x, int y, int w, int h,
            float fontSize = 10F, bool bold = false, Color? color = null)
        {
            var lbl = new Label
            {
                Text      = text,
                Location  = new Point(x, y),
                Size      = new Size(w, h),
                ForeColor = color ?? Color.FromArgb(0, 255, 170),
                Font      = new Font("Segoe UI", fontSize,
                                bold ? FontStyle.Bold : FontStyle.Regular)
            };
            Controls.Add(lbl);
            return lbl;
        }

        private int AddInfoRow(string key, string value, int y)
        {
            AddLabel($"{key}:", 20, y, 180, 22, 10F, color: Color.Cyan);
            AddLabel(value,     210, y, 380, 22, 10F, color: Color.White);
            return y + 26;
        }
    }
}