import unittest
from unittest.mock import patch, MagicMock
import sys
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Загружаем .env из корня проекта
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "config.env"))

from trader import Trader

class TestTraderOpen(unittest.TestCase):

    def setUp(self):
        """Создаём Trader с замоканным клиентом Binance"""
        # Мокаем клиент, чтобы не требовались реальные API ключи
        with patch('trader.Client') as mock_client:
            self.trader = Trader()
            self.trader.client = MagicMock()

    @patch('trader.insert_open_trade')
    def test_open_long_position(self, mock_insert):
        """Тест открытия Long позиции"""
        mock_insert.return_value = 999

        success, message = self.trader.open_trade(
            pair="ALGOUSDT",
            entry=0.1123,
            stop=0.1118,
            take=0.1144,
            reason_entry="Тестовое открытие Long из unit-теста",
            fear_greed=55,
            direction="long",
            leverage=20,
            risk_dollar=10.0,
            risk_percent=2.0
        )

        self.assertTrue(success, "Позиция должна успешно открыться")
        self.assertIn("успешно отправлен", message.lower())
        mock_insert.assert_called_once()

    @patch('trader.insert_open_trade')
    def test_open_short_position(self, mock_insert):
        """Тест открытия Short позиции"""
        mock_insert.return_value = 1000

        success, message = self.trader.open_trade(
            pair="ALGOUSDT",
            entry=0.1123,
            stop=0.1130,
            take=0.1100,
            reason_entry="Тестовое открытие Short",
            fear_greed=60,
            direction="short",
            leverage=15,
            risk_dollar=15.0,
            risk_percent=3.0
        )

        self.assertTrue(success)
        self.assertIn("успешно отправлен", message.lower())

    def test_open_trade_with_bad_rr(self):
        """Тест: позиция не должна открываться при RR < 3"""
        success, message = self.trader.open_trade(
            pair="ALGOUSDT",
            entry=0.1125,
            stop=0.1118,
            take=0.1130,        # слишком маленький тейк (ошибка будет ОК)
            reason_entry="Плохой RR",
            fear_greed=50,
            direction="long",
            leverage=20,
            risk_dollar=10.0,
            risk_percent=2.0
        )

        self.assertFalse(success)
        self.assertIn("RR", message)
        self.assertIn("< 3", message)


if __name__ == '__main__':
    unittest.main(verbosity=2)