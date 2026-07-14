import unittest
from unittest.mock import MagicMock
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "config.env"))
from trader import Trader

class TestTraderClose(unittest.TestCase):

    def setUp(self):
        self.trader = Trader()
        self.trader.client = MagicMock()

    def test_close_existing_position(self):
        """Тест успешного закрытия позиции"""
        self.trader.client.futures_position_information.return_value = [
            {'symbol': 'ALGOUSDT', 'positionAmt': '5.0', 'positionSide': 'BOTH'}
        ]
        self.trader.client.futures_create_order.return_value = {"orderId": 12345}

        success, message = self.trader.close_trade(
            pair="ALGOUSDT",
            reason_close="Тестовое закрытие по тейку"
        )

        self.assertTrue(success)
        self.assertIn("закрыта", message.lower())

        self.trader.client.futures_create_order.assert_called_once()

    def test_close_nonexistent_position(self):
        """Тест: попытка закрыть несуществующую позицию"""

        self.trader.client.futures_position_information.return_value = [
            {'symbol': 'BTCUSDT', 'positionAmt': '0'}
        ]

        success, message = self.trader.close_trade(
            pair="UNKNOWNUSDT",
            reason_close="Попытка закрыть несуществующую позицию"
        )

        self.assertFalse(success)
        self.assertIn("не найдена", message.lower())

if __name__ == '__main__':
    unittest.main(verbosity=2)
