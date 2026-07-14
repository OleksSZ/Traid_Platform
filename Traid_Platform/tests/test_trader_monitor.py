import unittest
from unittest.mock import MagicMock
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "config.env"))

from trader import Trader

class TestTraderMonitor(unittest.TestCase):

    def setUp(self):
        self.trader = Trader()
        self.trader.client = MagicMock()

    def test_get_open_positions_with_multiple(self):
        """Тест: мониторинг возвращает список строк с тикерами"""
        self.trader.client.futures_position_information.return_value = [
            {'symbol': 'ALGOUSDT', 'positionAmt': '-5.0', 'entryPrice': '0.1123'},
            {'symbol': 'BTCUSDT', 'positionAmt': '0.001', 'entryPrice': '65000'},
            {'symbol': 'ETHUSDT', 'positionAmt': '2.5', 'entryPrice': '3200'}
        ]

        positions = self.trader.get_open_positions()

        # Проверяем количество
        self.assertEqual(len(positions), 3)

        # Проверяем, что строки содержат тикеры
        self.assertTrue(any("ALGOUSDT" in p for p in positions))
        self.assertTrue(any("BTCUSDT" in p for p in positions))
        self.assertTrue(any("ETHUSDT" in p for p in positions))

        # Проверяем, что есть указание стороны (long/short)
        self.assertTrue(any("LONG" in p or "SHORT" in p for p in positions))

    def test_get_open_positions_filters_zero(self):
        """Тест: позиции с нулевым количеством должны отбрасываться"""
        self.trader.client.futures_position_information.return_value = [
            {'symbol': 'ALGOUSDT', 'positionAmt': '0', 'entryPrice': '0.1123'},
            {'symbol': 'BTCUSDT', 'positionAmt': '0.001', 'entryPrice': '65000'}
        ]

        positions = self.trader.get_open_positions()

        self.assertEqual(len(positions), 1)

        self.assertIn("BTCUSDT", positions[0])
        self.assertTrue("LONG" in positions[0] or "SHORT" in positions[0])

if __name__ == '__main__':
    unittest.main(verbosity=2)
