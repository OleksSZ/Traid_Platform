using System;
using System.Drawing;
using System.Windows.Forms;

namespace HighTechTrader
{
    /// <summary>
    /// Діалог закриття позиції — успадковує Form.
    /// </summary>
    public class CloseTradeDialog : Form
    {
        public string SelectedPair   { get; private set; }
        public string CloseReason    { get; private set; }

        private ComboBox cmbPositions;
        private TextBox  txtReason;
        private Button   btnOK;
        private Button   btnCancel;

        public CloseTradeDialog(string[] openPositions)
        {
            InitializeComponent();
            cmbPositions.Items.AddRange(openPositions);
            if (cmbPositions.Items.Count > 0)
                cmbPositions.SelectedIndex = 0;
        }

        private void btnOK_Click(object sender, EventArgs e)
        {
            if (cmbPositions.SelectedItem == null)
            {
                MessageBox.Show("Оберіть позицію!", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            if (string.IsNullOrWhiteSpace(txtReason.Text))
            {
                MessageBox.Show("Вкажіть причину закриття!", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            SelectedPair = cmbPositions.SelectedItem.ToString().Split(' ')[0];
            CloseReason  = txtReason.Text.Trim();
            DialogResult = DialogResult.OK;
            Close();
        }

        private void InitializeComponent()
        {
            this.Text            = "🔴 Закриття позиції";
            this.BackColor       = Color.FromArgb(10, 10, 15);
            this.ForeColor       = Color.Cyan;
            this.Font            = new Font("Segoe UI", 10F);
            this.ClientSize      = new Size(480, 260);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox     = false;
            this.StartPosition   = FormStartPosition.CenterParent;

            AddLabel("Оберіть позицію:", 20, 20);

            cmbPositions = new ComboBox
            {
                Location      = new Point(20, 44),
                Size          = new Size(440, 30),
                DropDownStyle = ComboBoxStyle.DropDownList,
                BackColor     = Color.FromArgb(20, 20, 30),
                ForeColor     = Color.White,
                FlatStyle     = FlatStyle.Flat
            };
            Controls.Add(cmbPositions);

            AddLabel("Причина закриття:", 20, 90);

            txtReason = new TextBox
            {
                Multiline   = true,
                Location    = new Point(20, 114),
                Size        = new Size(440, 60),
                BackColor   = Color.FromArgb(20, 20, 30),
                ForeColor   = Color.White,
                BorderStyle = BorderStyle.FixedSingle,
                PlaceholderText = "TP досягнутий / SL спрацював / Вручну..."
            };
            Controls.Add(txtReason);

            btnOK = new Button
            {
                Text      = "✅ Закрити",
                Location  = new Point(20, 192),
                Size      = new Size(200, 42),
                BackColor = Color.FromArgb(150, 0, 0),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font      = new Font("Segoe UI", 11F, FontStyle.Bold)
            };
            btnOK.FlatAppearance.BorderSize = 0;
            btnOK.Click += btnOK_Click;
            Controls.Add(btnOK);

            btnCancel = new Button
            {
                Text      = "Скасувати",
                Location  = new Point(260, 192),
                Size      = new Size(200, 42),
                BackColor = Color.FromArgb(40, 40, 60),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font      = new Font("Segoe UI", 11F)
            };
            btnCancel.FlatAppearance.BorderSize = 0;
            btnCancel.Click += (_, __) => { DialogResult = DialogResult.Cancel; Close(); };
            Controls.Add(btnCancel);
        }

        private void AddLabel(string text, int x, int y)
        {
            Controls.Add(new Label
            {
                Text     = text,
                Location = new Point(x, y),
                AutoSize = true,
                ForeColor = Color.Cyan,
                Font     = new Font("Segoe UI", 10F)
            });
        }
    }
}