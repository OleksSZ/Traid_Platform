import sys
import os
from dotenv import load_dotenv, set_key
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTextEdit, QLabel, QLineEdit, QInputDialog, QMessageBox,
    QDialog, QComboBox, QDialogButtonBox, QGridLayout, QGroupBox,
    QSpinBox, QFileDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

from trader import Trader
from database import init_journal, insert_open_trade, get_open_positions, close_trade
from leverage import calculate_optimal_leverage
import subprocess
from checks import check_rr, get_position_size

load_dotenv(dotenv_path='config.env')


class OpenTradeDialog(QDialog):
    def __init__(self, parent, pair, direction, entry, stop, take, leverage, risk_usd, risk_percent=None):
        super().__init__(parent)
        self.setWindowTitle("🟢 Открытие позиции — Дневник трейдера")
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)
        self.setStyleSheet(parent.styleSheet())

        self.pair = pair
        self.direction = direction.lower()
        self.entry = float(entry)
        self.stop = float(stop)
        self.take = float(take)
        self.leverage = leverage
        self.risk_usd = float(risk_usd)
        self.risk_percent = float(risk_percent) if risk_percent is not None else None

        # Проверка RR сразу
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
        layout.setSpacing(15)

        title = QLabel(f"Открытие {self.pair} — {self.direction.upper()}")
        title.setStyleSheet("font-size: 26px; color: lime; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Параметры сделки
        info_gb = QGroupBox("Параметры сделки")
        grid = QGridLayout()

        rows = [
            ("Пара", self.pair),
            ("Направление", self.direction.capitalize()),
            ("Цена входа", f"{self.entry:.4f}"),
            ("Stop-Loss", f"{self.stop:.4f}"),
            ("Take-Profit", f"{self.take:.4f}"),
            ("Плечо", f"{self.leverage}x"),
            ("Риск на сделку ($)", f"${self.risk_usd:.2f}"),
            ("Риск % от депозита", f"{self.risk_percent:.2f}%" if self.risk_percent else "—"),
            ("RR Ratio", f"{self.rr:.2f}"),
            ("Потенциальная прибыль", f"+${self.potential_profit}"),
            ("Потенциальный убыток", f"${self.potential_loss}"),
        ]

        for i, (label, value) in enumerate(rows):
            grid.addWidget(QLabel(f"<b>{label}:</b>"), i, 0)
            color = "lime" if self.rr_ok else "red"
            grid.addWidget(QLabel(f"<b style='color:{color}'>{value}</b>"), i, 1)

        info_gb.setLayout(grid)
        layout.addWidget(info_gb)

        if not self.rr_ok:
            warning = QLabel(f"⚠️ {self.rr_message}")
            warning.setStyleSheet("color: red; font-weight: bold; font-size: 15px;")
            layout.addWidget(warning)

        # Дневник трейдера
        input_gb = QGroupBox("Дневник трейдера")
        form = QGridLayout()

        form.addWidget(QLabel("Причина входа:"), 0, 0)
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("Почему ты решил открыть эту позицию? (необязательно)")
        self.reason_input.setMaximumHeight(80)
        form.addWidget(self.reason_input, 0, 1)

        form.addWidget(QLabel("Fear & Greed (0-100):"), 1, 0)
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

        # Новое поле — ссылка на TradingView
        form.addWidget(QLabel("Ссылка на TradingView:"), 3, 0)
        self.tv_link_input = QLineEdit()
        self.tv_link_input.setPlaceholderText("https://www.tradingview.com/chart/... (необязательно)")
        form.addWidget(self.tv_link_input, 3, 1)

        input_gb.setLayout(form)
        layout.addWidget(input_gb)

        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._validate)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _validate(self):
        # Проверка RR перед отправкой
        ok, msg, _, _ = check_rr(self.entry, self.stop, self.take, self.direction)
        if not ok:
            QMessageBox.warning(self, "Ошибка RR", msg)
            return  # Не закрываем окно
        # if not self.reason_input.toPlainText().strip():
        #     QMessageBox.warning(self, "Ошибка", "Причина входа обязательна!")
        #     return  #Часть отвещающая за обязательную проверку причыны входа ( Что там что-то есть в поле )

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

        # Стиль оформления
        self.app.setStyleSheet("""
            QWidget {
                background-color: black;
                color: limegreen;
                font-family: Courier New;
                font-size: 18px;
                font-weight: bold;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: rgba(30,30,30,200);
                border: 2px solid rgba(0,255,0,150);
                color: limegreen;
                padding: 6px;
            }
            QPushButton {
                background-color: rgba(0,51,0,180);
                border: 2px solid rgba(0,255,0,150);
                padding: 14px;
                color: limegreen;
            }
            QPushButton:hover {
                background-color: rgba(0,102,0,200);
            }
            QLabel {
                color: limegreen;
            }
            QGroupBox {
                border: 2px solid rgba(0,255,0,100);
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        self.window = QMainWindow()
        self.window.setWindowTitle("Интерактивный Трейдер")
        self.window.resize(1250, 850)
        self.window.setMinimumSize(800, 500)
        self.window.setWindowIcon(QIcon("trader.ico"))

        central_widget = QWidget()
        layout = QVBoxLayout()

        # Поля ввода
        layout.addWidget(QLabel("Пара (например, BTCUSDT):"))
        self.pair_input = QLineEdit("BTCUSDT")
        layout.addWidget(self.pair_input)

        layout.addWidget(QLabel("Направление позиции:"))
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Long", "Short"])
        layout.addWidget(self.direction_combo)

        layout.addWidget(QLabel("Цена входа:"))
        self.entry_input = QLineEdit()
        layout.addWidget(self.entry_input)

        layout.addWidget(QLabel("Стоп-лосс:"))
        self.stop_input = QLineEdit()
        layout.addWidget(self.stop_input)

        layout.addWidget(QLabel("Тейк-профит:"))
        self.take_input = QLineEdit()
        layout.addWidget(self.take_input)

        # === Новый параметр: Процент риска от депозита ===
        layout.addWidget(QLabel("Процент риска от депозита (%):"))
        self.risk_percent_input = QLineEdit("1.0")
        layout.addWidget(self.risk_percent_input)

        layout.addWidget(QLabel("Или риск на сделку ($) :"))
        self.risk_input = QLineEdit("100")
        layout.addWidget(self.risk_input)

        # Кнопка Freqtrade
        freqtrade_button = QPushButton("🚀 Открыть Freqtrade Constructor (Streamlit)")
        freqtrade_button.setStyleSheet("""
            QPushButton { background-color: rgba(0, 100, 200, 180); border: 2px solid rgba(0, 200, 255, 200); padding: 16px; }
            QPushButton:hover { background-color: rgba(0, 120, 220, 200); }
        """)
        freqtrade_button.clicked.connect(self.open_freqtrade_interface)
        layout.addWidget(freqtrade_button)

        # Основные кнопки
        open_button = QPushButton("Открыть позицию (проверить условия)")
        open_button.clicked.connect(self.open_trade)
        layout.addWidget(open_button)

        close_button = QPushButton("Закрыть позицию")
        close_button.clicked.connect(self.show_close_menu)
        layout.addWidget(close_button)

        monitor_button = QPushButton("Старт мониторинга")
        monitor_button.clicked.connect(self.start_monitoring)
        layout.addWidget(monitor_button)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        central_widget.setLayout(layout)
        self.window.setCentralWidget(central_widget)
        self.window.show()

        self._load_saved_risk()

        # Инициализация
        init_journal()
        self.trader = Trader()
        self.trader.check_closed_trades()

        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_trades)

    def _load_saved_risk(self):
        # Загружаем процент риска
        saved_percent = os.getenv('RISK_PERCENT')
        if saved_percent:
            try:
                self.risk_percent_input.setText(f"{float(saved_percent):.2f}")
            except:
                self.risk_percent_input.setText("1.0")

        # Загружаем риск в долларах
        saved_risk = os.getenv('RISK_PER_TRADE_USD')
        if saved_risk:
            try:
                self.risk_input.setText(f"{float(saved_risk):.2f}")
            except:
                self.risk_input.setText("100")

    def open_freqtrade_interface(self):
        try:
            freqtrade_folder = r"D:\Trading\freqtrade"
            interface_path = os.path.join(freqtrade_folder, "Interface.py")
            python_exe = r"D:\Trading\freqtrade\.venv\Scripts\python.exe"

            if not os.path.exists(interface_path) or not os.path.exists(python_exe):
                QMessageBox.critical(self.window, "Ошибка", "Не найден путь к Freqtrade или python.exe")
                return

            subprocess.Popen(
                [python_exe, "-m", "streamlit", "run", interface_path,
                 "--server.port=8501", "--server.headless=false", "--server.address=127.0.0.1"],
                cwd=freqtrade_folder,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            self.log_output.append("✅ Streamlit запущен")
            import webbrowser
            QTimer.singleShot(5000, lambda: webbrowser.open("http://localhost:8501"))

        except Exception as e:
            QMessageBox.critical(self.window, "Ошибка запуска", str(e))

    def open_trade(self):
        pair = self.pair_input.text().strip().upper()
        direction = self.direction_combo.currentText().lower()

        try:
            entry = float(self.entry_input.text())
            stop = float(self.stop_input.text())
            take = float(self.take_input.text())
            risk_percent = float(self.risk_percent_input.text())
            risk_usd = float(self.risk_input.text())

            if risk_percent <= 0 or risk_usd <= 0:
                raise ValueError("Риск должен быть положительным")
        except ValueError:
            QMessageBox.warning(self.window, "Ошибка ввода", 
                                "Все числовые поля должны быть положительными числами!")
            return

        # Сохраняем настройки риска
        try:
            set_key('config.env', 'RISK_PERCENT', str(risk_percent))
            set_key('config.env', 'RISK_PER_TRADE_USD', str(risk_usd))
        except:
            pass

        # Расчёт плеча
        try:
            leverage = calculate_optimal_leverage(entry, stop, risk_usd, risk_percent)
            self.log_output.append(f"→ Рассчитанное плечо: {leverage}x")
        except Exception as e:
            QMessageBox.warning(self.window, "Ошибка расчёта плеча", str(e))
            return

        if leverage > 50:
            reply = QMessageBox.question(self.window, "Высокое плечо!", 
                                        f"Вы уверены, что хотите использовать {leverage}x?\nЭто очень агрессивно!",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # Открываем модальное окно
        dialog = OpenTradeDialog(
            self.window, pair, direction, entry, stop, take, leverage, risk_usd, risk_percent
        )
        
        if dialog.exec_() == QDialog.Accepted:
            trade_data = dialog.get_data()

            success, message = self.trader.open_trade(
                pair=pair,
                entry=entry,
                stop=stop,
                take=take,
                reason_entry=trade_data.get('reason_entry', ''),
                fear_greed=trade_data.get('fear_greed', 50),
                direction=direction,
                leverage=leverage,
                risk_dollar=risk_usd,
                risk_percent=risk_percent
            )

            self.log_output.append(message)

            if success:
                try:
                    # Сохраняем только в Excel-таблицу (без Telegram)
                    insert_open_trade(trade_data)
                    self.log_output.append(f"✅ Позиция успешно записана в trade_journal.xlsx")
                except Exception as e:
                    self.log_output.append(f"⚠️ Ошибка сохранения в журнал: {e}")
            else:
                self.log_output.append("❌ Позиция не открыта")
        else:
            self.log_output.append("Открытие позиции отменено")

    def show_close_menu(self):
        open_pos = self.trader.get_open_positions()
        if not open_pos:
            QMessageBox.information(self.window, "Инфо", "Нет открытых позиций.")
            return

        dialog = QDialog(self.window)
        dialog.setWindowTitle("Закрытие позиции")
        layout = QVBoxLayout()

        combo = QComboBox()
        combo.addItems(open_pos)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        if dialog.exec_() == QDialog.Accepted:
            selected = combo.currentText()
            pair = selected.split(' ')[0]

            reason_close, ok = QInputDialog.getText(self.window, "Дневник", "Причина закрытия:")
            if not ok or not reason_close.strip():
                QMessageBox.warning(self.window, "Ошибка", "Причина закрытия обязательна!")
                return

            success, message = self.trader.close_trade(pair, reason_close)
            self.log_output.append(message)

    def monitor_trades(self):
        positions_info = self.trader.monitor_trades()
        self.log_output.clear()
        self.log_output.append(positions_info)

    def start_monitoring(self):
        if not self.monitor_timer.isActive():
            self.monitor_timer.start(3000)
            self.log_output.append("Мониторинг запущен (каждые 3 секунды)")
        else:
            self.monitor_timer.stop()
            self.log_output.append("Мониторинг остановлен")

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    gui = TraderGUI()
    gui.run()