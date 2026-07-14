# gui.py
import sys
import os
from dotenv import load_dotenv, set_key
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTextEdit, QLabel, QInputDialog, QMessageBox,
    QDialog, QComboBox, QDialogButtonBox, QGridLayout, QGroupBox,
    QSpinBox, QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

from trader import Trader
from database import init_journal
from leverage import calculate_optimal_leverage
import subprocess
from checks import check_rr
from parcer import get_usdt_balance
from orderbook_window import OrderBookWindow

load_dotenv(dotenv_path='config.env')


class OpenTradeDialog(QDialog):
    def __init__(self, parent, pair, direction, entry, stop, take, leverage, risk_usd, risk_percent=None):
        super().__init__(parent)
        self.setWindowTitle("🟢 Открытие позиции")
        self.setMinimumWidth(800)
        self.setMinimumHeight(680)
        self.setStyleSheet(parent.styleSheet())

        self.pair = pair
        self.direction = direction.lower()
        self.entry = float(entry)
        self.stop = float(stop)
        self.take = float(take)
        self.leverage = leverage
        self.risk_usd = float(risk_usd)
        self.risk_percent = float(risk_percent) if risk_percent is not None else None

        self.rr_ok, self.rr_message, self.risk, self.reward = check_rr(self.entry, self.stop, self.take, self.direction)

        if self.direction == "long":
            self.rr = (self.take - self.entry) / (self.entry - self.stop) if (self.entry - self.stop) != 0 else 0
        else:
            self.rr = (self.entry - self.take) / (self.stop - self.entry) if (self.stop - self.entry) != 0 else 0

        self.potential_profit = round(self.risk_usd * self.rr, 2)
        self.potential_loss = -self.risk_usd

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(f"Открытие {self.pair} — {self.direction.upper()}")
        title.setStyleSheet("font-size: 24px; color: #00ffaa; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        info_gb = QGroupBox("📋 Параметры сделки")
        grid = QGridLayout()
        grid.setVerticalSpacing(8)

        rows = [
            ("Пара", self.pair),
            ("Направление", self.direction.capitalize()),
            ("Цена входа", f"{self.entry:.4f}"),
            ("Stop-Loss", f"{self.stop:.4f}"),
            ("Take-Profit", f"{self.take:.4f}"),
            ("Плечо", f"{self.leverage}x"),
            ("Риск ($)", f"${self.risk_usd:.2f}"),
            ("Риск %", f"{self.risk_percent:.2f}%" if self.risk_percent else "—"),
            ("RR", f"{self.rr:.2f}"),
            ("Прибыль", f"+${self.potential_profit}"),
            ("Убыток", f"${self.potential_loss}"),
        ]

        for i, (label, value) in enumerate(rows):
            grid.addWidget(QLabel(f"<b>{label}:</b>"), i, 0)
            color = "#00ffaa" if self.rr_ok else "#ff4444"
            grid.addWidget(QLabel(f"<b style='color:{color}'>{value}</b>"), i, 1)

        info_gb.setLayout(grid)
        layout.addWidget(info_gb)

        if not self.rr_ok:
            warning = QLabel(f"⚠️ {self.rr_message}")
            warning.setStyleSheet("color: #ff4444; font-weight: bold;")
            layout.addWidget(warning)

        input_gb = QGroupBox("📖 Дневник трейдера")
        form = QGridLayout()
        form.setVerticalSpacing(10)

        form.addWidget(QLabel("Причина входа:"), 0, 0)
        self.reason_input = QTextEdit()
        self.reason_input.setMaximumHeight(70)
        self.reason_input.setPlaceholderText("Почему открываем позицию?")
        form.addWidget(self.reason_input, 0, 1)

        form.addWidget(QLabel("Fear & Greed:"), 1, 0)
        self.fg_spin = QSpinBox()
        self.fg_spin.setRange(0, 100)
        self.fg_spin.setValue(50)
        form.addWidget(self.fg_spin, 1, 1)

        form.addWidget(QLabel("Шанс на профит (%):"), 2, 0)
        self.shans_spin = QSpinBox()
        self.shans_spin.setRange(0, 100)
        self.shans_spin.setValue(65)
        self.shans_spin.setSuffix("%")
        form.addWidget(self.shans_spin, 2, 1)

        form.addWidget(QLabel("TradingView ссылка:"), 3, 0)
        self.tv_link_input = QLineEdit()
        self.tv_link_input.setPlaceholderText("https://www.tradingview.com/chart/...")
        form.addWidget(self.tv_link_input, 3, 1)

        input_gb.setLayout(form)
        layout.addWidget(input_gb)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _validate(self):
        ok, msg, _, _ = check_rr(self.entry, self.stop, self.take, self.direction)
        if not ok:
            QMessageBox.warning(self, "Ошибка RR", msg)
            return
        self.accept()

    def get_data(self):
        return {
            'pair': self.pair,
            'direction': self.direction,
            'entry_price': self.entry,
            'stop_loss': self.stop,
            'take_profit': self.take,
            'leverage': self.leverage,
            'rr_ratio': round(self.rr, 4),
            'potential_profit': self.potential_profit,
            'potential_loss': self.potential_loss,
            'risk_usd': round(self.risk_usd, 2),
            'risk_percent': round(self.risk_percent, 2) if self.risk_percent else None,
            'reason_entry': self.reason_input.toPlainText().strip(),
            'fear_greed': self.fg_spin.value(),
            'profit_shans': self.shans_spin.value(),
            'tradingview_link': self.tv_link_input.text().strip() or None,
        }


class TraderGUI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(self.high_tech_stylesheet())

        self.window = QMainWindow()
        self.window.setWindowTitle("🔥 HIGH-TECH TRADER v2.2")
        self.window.resize(1420, 820)
        self.window.setMinimumSize(1150, 680)

        # Загружаем список активных пар из файла
        self.pairs = self.load_active_pairs()

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # ====================== ЛЕВАЯ ЧАСТЬ ======================
        left = QVBoxLayout()
        left.setSpacing(8)

        # Поле "Пара" — ComboBox с возможностью ввода
        left.addWidget(QLabel("🔹 Пара"))
        self.pair_combo = QComboBox()
        self.pair_combo.setEditable(True)
        self.pair_combo.setInsertPolicy(QComboBox.InsertAtTop)
        self.pair_combo.addItems(self.pairs)
        self.pair_combo.setCurrentText("BTCUSDT")
        left.addWidget(self.pair_combo)

        left.addWidget(QLabel("🔹 Направление позиции"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Long", "Short"])
        left.addWidget(self.direction_combo)

        left.addWidget(QLabel("🔹 Цена входа"))
        self.entry_input = QLineEdit()
        self.entry_input.setFixedHeight(32)
        left.addWidget(self.entry_input)

        left.addWidget(QLabel("🔹 Stop-Loss"))
        self.stop_input = QLineEdit()
        self.stop_input.setFixedHeight(32)
        left.addWidget(self.stop_input)

        left.addWidget(QLabel("🔹 Take-Profit"))
        self.take_input = QLineEdit()
        self.take_input.setFixedHeight(32)
        left.addWidget(self.take_input)

        left.addWidget(QLabel("🔹 Риск % от депозита"))
        self.risk_percent_input = QLineEdit("1.0")
        self.risk_percent_input.setFixedHeight(32)
        left.addWidget(self.risk_percent_input)

        left.addWidget(QLabel("🔹 Риск на сделку ($)"))
        self.risk_input = QLineEdit("0.20")
        self.risk_input.setFixedHeight(32)
        left.addWidget(self.risk_input)

        # Кнопки
        btns = [
            ("🚀 Freqtrade Constructor", self.open_freqtrade_interface, "#003366"),
            ("🟢 Открыть позицию", self.open_trade, "#004400"),
            ("🔴 Закрыть позицию", self.show_close_menu, "#660000"),
            ("📡 Мониторинг (3 сек)", self.start_monitoring, "#224400"),
            ("📊 LIVE Order Book", self.open_order_book, "#002244"),
        ]

        for text, func, color in btns:
            btn = QPushButton(text)
            btn.setFixedHeight(38)
            btn.setStyleSheet(f"background-color: {color};")
            btn.clicked.connect(func)
            left.addWidget(btn)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(180)
        left.addWidget(self.log_output)

        main_layout.addLayout(left, 62)

        # ====================== ПРАВАЯ ПАНЕЛЬ ======================
        right = QVBoxLayout()
        right.setSpacing(12)

        balance_group = QGroupBox("💰 Фьючерсный баланс USDT")
        bl = QVBoxLayout()
        self.balance_label = QLabel("Загрузка...")
        self.balance_label.setStyleSheet("font-size: 18px; color: #00ffff; padding: 8px;")
        bl.addWidget(self.balance_label)
        balance_group.setLayout(bl)
        right.addWidget(balance_group)

        right.addStretch()

        footer = QLabel("High-Tech Trader • WebSocket Order Book + Real-time Balance")
        footer.setStyleSheet("color: #555555; font-size: 13px;")
        footer.setAlignment(Qt.AlignCenter)
        right.addWidget(footer)

        main_layout.addLayout(right, 38)

        self.window.setCentralWidget(central)
        self.window.show()

        self._load_saved_risk()
        init_journal()
        self.trader = Trader()
        self.trader.check_closed_trades()

        self.balance_timer = QTimer()
        self.balance_timer.timeout.connect(self.update_balance)
        self.balance_timer.start(5000)

        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_trades)

        self.update_balance()

    def load_active_pairs(self):
        """Загружает пары из active_pairs.txt"""
        default_pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "CAKEUSDT", "XRPUSDT"]
        pairs_file = "active_pairs.txt"

        if os.path.exists(pairs_file):
            try:
                with open(pairs_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        loaded = [p.strip().upper() for p in content.split(",") if p.strip()]
                        if loaded:
                            return loaded
            except Exception as e:
                print(f"Ошибка чтения active_pairs.txt: {e}")
        return default_pairs

    def high_tech_stylesheet(self):
        return """
            QWidget {
                background-color: #0a0a0a;
                color: #00ffaa;
                font-family: 'Consolas', monospace;
                font-size: 16px;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #111111;
                border: 2px solid #00cccc;
                color: #00ffcc;
                padding: 6px 8px;
                border-radius: 5px;
            }
            QPushButton {
                border: 2px solid #00ff88;
                padding: 8px;
                color: #00ffaa;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00aa44;
                color: white;
            }
            QGroupBox {
                border: 2px solid #00ffff;
                margin-top: 10px;
                color: #00ffff;
            }
        """

    def update_balance(self):
        try:
            bal = get_usdt_balance()
            if bal:
                self.balance_label.setText(
                    f"Всего: <b>${bal['total']:.2f}</b><br>"
                    f"Доступно: <span style='color:#00ffcc'>${bal['available']:.2f}</span><br>"
                    f"В позициях: <span style='color:#ff6666'>${bal['used']:.2f}</span>"
                )
            else:
                self.balance_label.setText("❌ Не удалось получить баланс")
        except Exception as e:
            self.balance_label.setText(f"Ошибка: {str(e)[:60]}")

    def open_order_book(self):
        if not hasattr(self, 'orderbook_win') or not self.orderbook_win.isVisible():
            self.orderbook_win = OrderBookWindow(self.window)
        self.orderbook_win.show()
        self.orderbook_win.raise_()

    def open_freqtrade_interface(self):
        try:
            freqtrade_folder = r"D:\Trading\freqtrade"
            interface_path = os.path.join(freqtrade_folder, "Interface.py")
            python_exe = r"D:\Trading\freqtrade\.venv\Scripts\python.exe"

            if not os.path.exists(interface_path) or not os.path.exists(python_exe):
                QMessageBox.critical(self.window, "Ошибка", "Freqtrade не найден")
                return

            subprocess.Popen(
                [python_exe, "-m", "streamlit", "run", interface_path,
                 "--server.port=8501", "--server.headless=false"],
                cwd=freqtrade_folder,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.log_output.append("✅ Freqtrade Streamlit запущен")
            import webbrowser
            QTimer.singleShot(4000, lambda: webbrowser.open("http://localhost:8501"))
        except Exception as e:
            QMessageBox.critical(self.window, "Ошибка", str(e))

    def open_trade(self):
        pair = self.pair_combo.currentText().strip().upper()
        direction = self.direction_combo.currentText().lower()

        try:
            entry = float(self.entry_input.text())
            stop = float(self.stop_input.text())
            take = float(self.take_input.text())
            risk_percent = float(self.risk_percent_input.text())
            risk_usd = float(self.risk_input.text())
        except ValueError:
            QMessageBox.warning(self.window, "Ошибка", "Проверьте числовые поля!")
            return

        try:
            set_key('config.env', 'RISK_PERCENT', str(risk_percent))
            set_key('config.env', 'RISK_PER_TRADE_USD', str(risk_usd))
        except:
            pass

        try:
            leverage = calculate_optimal_leverage(entry, stop, risk_usd, risk_percent)
            self.log_output.append(f"→ Плечо: {leverage}x")
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка плеча", str(e))
            return

        dialog = OpenTradeDialog(self.window, pair, direction, entry, stop, take, leverage, risk_usd, risk_percent)
        if dialog.exec_() == QDialog.Accepted:
            trade_data = dialog.get_data()
            success, message = self.trader.open_trade(
                pair=pair, entry=entry, stop=stop, take=take,
                reason_entry=trade_data.get('reason_entry', ''),
                fear_greed=trade_data.get('fear_greed', 50),
                direction=direction, leverage=leverage,
                risk_dollar=risk_usd, risk_percent=risk_percent
            )
            self.log_output.append(message)

            if success:
                try:
                    from database import insert_open_trade
                    insert_open_trade(trade_data)
                    self.log_output.append("✅ Записано в журнал")
                except Exception as e:
                    self.log_output.append(f"⚠️ Ошибка журнала: {e}")

    def show_close_menu(self):
        open_pos = self.trader.get_open_positions()
        if not open_pos:
            QMessageBox.information(self.window, "Инфо", "Нет открытых позиций.")
            return

        dlg = QDialog(self.window)
        dlg.setWindowTitle("Закрытие позиции")
        layout = QVBoxLayout(dlg)

        combo = QComboBox()
        combo.addItems(open_pos)
        layout.addWidget(combo)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec_() == QDialog.Accepted:
            pair = combo.currentText().split()[0]
            reason, ok = QInputDialog.getText(self.window, "Причина", "Причина закрытия:")
            if ok and reason.strip():
                success, msg = self.trader.close_trade(pair, reason)
                self.log_output.append(msg)

    def monitor_trades(self):
        info = self.trader.monitor_trades()
        self.log_output.clear()
        self.log_output.append("=== Активные позиции ===\n" + (info or "Нет открытых позиций."))

    def start_monitoring(self):
        if not self.monitor_timer.isActive():
            self.monitor_timer.start(3000)
            self.log_output.append("✅ Мониторинг запущен")
        else:
            self.monitor_timer.stop()
            self.log_output.append("⏹️ Мониторинг остановлен")

    def _load_saved_risk(self):
        try:
            if os.getenv('RISK_PERCENT'):
                self.risk_percent_input.setText(f"{float(os.getenv('RISK_PERCENT')):.2f}")
            if os.getenv('RISK_PER_TRADE_USD'):
                self.risk_input.setText(f"{float(os.getenv('RISK_PER_TRADE_USD')):.2f}")
        except:
            pass

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    gui = TraderGUI()
    gui.run()