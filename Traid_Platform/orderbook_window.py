# orderbook_window.py
import sys
import json
import time
import threading
import websocket
import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor


class OrderBookWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 LIVE Order Book — Binance Futures (WS)")
        self.setMinimumSize(1000, 740)
        self.symbol = "BTCUSDT"
        self.ws = None
        self.ws_thread = None
        self.bids = []
        self.asks = []
        self.lock = threading.Lock()

        self.pairs_file = "active_pairs.txt"
        self.load_pairs()

        self.setup_ui()
        self.setStyleSheet(self.high_tech_style())

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_table)
        self.refresh_timer.start(300)

    def load_pairs(self):
        """Загружает пары из active_pairs.txt"""
        self.pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "CAKEUSDT"]  # запасные

        if os.path.exists(self.pairs_file):
            try:
                with open(self.pairs_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        loaded = [p.strip().upper() for p in content.split(",") if p.strip()]
                        if loaded:
                            self.pairs = loaded
            except Exception as e:
                print(f"Ошибка чтения active_pairs.txt: {e}")

    def high_tech_style(self):
        return """
            QMainWindow, QWidget {
                background-color: #0a0a0a;
                color: #00ffaa;
                font-family: 'Consolas', monospace;
                font-size: 15px;
            }
            QLineEdit, QComboBox {
                background-color: #111111;
                border: 2px solid #00ffff;
                color: #00ffff;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton {
                background-color: #111111;
                border: 2px solid #00ffff;
                color: #00ffff;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #00aa88;
                color: white;
            }
            QTableWidget {
                background-color: #0a0a0a;
                gridline-color: #003322;
                border: 2px solid #00ffff;
                font-size: 14.5px;
                alternate-background-color: #111111;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #00ffff;
                border: none;
                padding: 8px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #003322;
            }
        """

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Верхняя панель
        top = QHBoxLayout()

        top.addWidget(QLabel("Монета:"))

        # Выпадающий список + возможность писать своё
        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)           # можно писать своё
        self.symbol_combo.setInsertPolicy(QComboBox.InsertAtTop)
        self.symbol_combo.addItems(self.pairs)
        self.symbol_combo.setCurrentText(self.symbol)
        self.symbol_combo.setFixedWidth(180)
        top.addWidget(self.symbol_combo)

        btn_start = QPushButton("🚀 Запустить WebSocket")
        btn_start.clicked.connect(self.start_ws)
        top.addWidget(btn_start)

        btn_stop = QPushButton("⏹️ Остановить")
        btn_stop.clicked.connect(self.stop_ws)
        top.addWidget(btn_stop)

        layout.addLayout(top)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "BID Price", "BID USDT", "ASK USDT", "ASK Price"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Статус
        self.status_label = QLabel("🟡 WebSocket не подключён")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 15px; padding: 6px;")
        layout.addWidget(self.status_label)

        self.setCentralWidget(central)

    def start_ws(self):
        self.symbol = self.symbol_combo.currentText().strip().upper()
        if not self.symbol.endswith("USDT"):
            self.status_label.setText("❌ Только пары заканчивающиеся на USDT!")
            return

        self.stop_ws()
        self.status_label.setText(f"🔌 Подключение к {self.symbol}...")
        self.ws_thread = threading.Thread(target=self._ws_thread, daemon=True)
        self.ws_thread.start()

    def _ws_thread(self):
        def on_message(ws_app, message):
            try:
                data = json.loads(message)
                if 'b' in data and 'a' in data:
                    with self.lock:
                        self.bids = [[float(p), float(q)] for p, q in data['b'][:20]]
                        self.asks = [[float(p), float(q)] for p, q in data['a'][:20]]
            except:
                pass

        def on_open(ws_app):
            print(f"✅ WS Order Book открыт для {self.symbol}")

        url = f"wss://fstream.binance.com/ws/{self.symbol.lower()}@depth20@100ms"
        self.ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_close=lambda *args: None
        )
        self.ws.run_forever()

    def stop_ws(self):
        if self.ws:
            self.ws.close()
            self.ws = None
        self.status_label.setText("⏹️ WebSocket остановлен")

    def update_table(self):
        with self.lock:
            if not self.bids and not self.asks:
                return

            self.table.setRowCount(20)

            for i in range(20):
                # BID
                if i < len(self.bids):
                    price = self.bids[i][0]
                    qty_usdt = round(self.bids[i][0] * self.bids[i][1])
                    self.table.setItem(i, 0, QTableWidgetItem(f"{price:.4f}"))
                    self.table.setItem(i, 1, QTableWidgetItem(f"{qty_usdt:,}"))
                    for col in [0, 1]:
                        item = self.table.item(i, col)
                        if item:
                            item.setForeground(QColor(0, 255, 140))
                else:
                    for col in [0, 1]:
                        self.table.setItem(i, col, QTableWidgetItem(""))

                # ASK
                if i < len(self.asks):
                    price = self.asks[i][0]
                    qty_usdt = round(self.asks[i][0] * self.asks[i][1])
                    self.table.setItem(i, 2, QTableWidgetItem(f"{qty_usdt:,}"))
                    self.table.setItem(i, 3, QTableWidgetItem(f"{price:.4f}"))
                    for col in [2, 3]:
                        item = self.table.item(i, col)
                        if item:
                            item.setForeground(QColor(255, 90, 90))
                else:
                    for col in [2, 3]:
                        self.table.setItem(i, col, QTableWidgetItem(""))

            self.status_label.setText(
                f"✅ LIVE • {self.symbol} • {time.strftime('%H:%M:%S')}"
            )


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = OrderBookWindow()
    win.show()
    sys.exit(app.exec_())