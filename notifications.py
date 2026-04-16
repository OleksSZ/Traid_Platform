# notifications.py
import telebot
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime

class NotificationManager:
    def __init__(self, token: str, chat_id: str):
        self.bot = telebot.TeleBot(token)
        self.chat_id = chat_id
        os.makedirs("charts", exist_ok=True)

    def send_text(self, text: str):
        """Отправка простого текста"""
        try:
            self.bot.send_message(self.chat_id, text, parse_mode="HTML")
            print(f"[TG] Текст отправлен: {text[:100]}...")
        except Exception as e:
            print(f"[TG ERROR] {e}")

    def send_chart(self, df, symbol: str, signal_type: str = None, caption: str = None):
        """Рисует график с помощью matplotlib и отправляет в TG"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Рисуем свечи
            for i in range(len(df)):
                o = df['open'].iloc[i]
                h = df['high'].iloc[i]
                l = df['low'].iloc[i]
                c = df['close'].iloc[i]
                color = 'green' if c >= o else 'red'
                ax.plot([i, i], [l, h], color='black', linewidth=1)
                ax.add_patch(plt.Rectangle((i-0.3, min(o,c)), 0.6, abs(c-o), color=color))

            ax.set_title(f"{symbol} — {signal_type if signal_type else 'График'}")
            ax.grid(True, alpha=0.3)

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
            buffer.seek(0)
            plt.close(fig)

            # Сохраняем локально
            filename = f"charts/{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(filename, "wb") as f:
                f.write(buffer.getvalue())

            # Отправляем в Telegram
            full_caption = caption or f"📊 {symbol} | {signal_type or 'Обновление'}"
            buffer.seek(0)
            self.bot.send_photo(self.chat_id, buffer, caption=full_caption, parse_mode="HTML")
            
            print(f"[TG] График отправлен: {symbol}")

        except Exception as e:
            print(f"[TG CHART ERROR] {e}")

    def send_log(self, message: str):
        """Отправка отладочных логов"""
        self.send_text(f"🔍 <i>Log:</i> {message}")

    def send_status(self, status: str):
        """Отправка статуса мониторинга"""
        self.send_text(f"📡 <b>Статус:</b> {status}")