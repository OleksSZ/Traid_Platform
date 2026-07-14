# test_journal_simple.py
# Положи этот файл в корень проекта (рядом с gui.py)

import unittest
import os
import pandas as pd
from datetime import datetime

# Добавляем путь к проекту
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import insert_open_trade, init_journal

class TestTradeJournalSimple(unittest.TestCase):

    def setUp(self):
        self.test_file = "test_trade_journal_temp.xlsx"
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

        # Временно меняем файл журнала для теста
        import database
        database.JOURNAL_FILE = self.test_file

        init_journal()

    def tearDown(self):
        if os.path.exists(self.test_file):
            try:
                os.remove(self.test_file)
            except:
                pass

    def test_can_save_trade(self):
        """Простой тест: можно ли сохранить сделку в журнал"""
        trade_data = {
            'pair': 'CAKEUSDT',
            'direction': 'LONG',
            'entry_price': 1.5286,
            'stop_loss': 1.5096,
            'take_profit': 1.5701,
            'leverage': 24,
            'rr_ratio': 3.76,
            'risk_dollar': 0.20,
            'risk_percent': 6.0,
            'reason_entry': 'Тест из простого unit-теста',
            'fear_greed': 50,
            'profit_shans': 65,
            'tradingview_link': None
        }

        trade_id = insert_open_trade(trade_data)

        self.assertIsNotNone(trade_id, "Должен вернуться ID записи")

        self.assertTrue(os.path.exists(self.test_file), "Файл журнала должен быть создан")

        df = pd.read_excel(self.test_file)
        self.assertEqual(len(df), 1, "Должна быть одна запись")

        row = df.iloc[0]
        self.assertEqual(row['pair'], 'CAKEUSDT')
        self.assertEqual(row['direction'], 'LONG')

        print(f"✅ Тест прошёл успешно! Сохранена позиция с ID {trade_id}")

if __name__ == '__main__':
    unittest.main(verbosity=2)