#  тестим checks.py
import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from checks import check_rr

class TestCheckRR(unittest.TestCase):

    def test_long_good_rr(self):
        """Long: хороший RR (1:4) → должен пройти"""
        ok, msg, risk, reward = check_rr(entry=100, stop=90, take=140, direction='long')
        self.assertTrue(ok, f"Ожидали OK, но получили: {msg}")
        self.assertGreaterEqual(reward / risk, 3.0, "RR должен быть >= 3.0")

    def test_long_bad_rr(self):
        """Long: плохой RR (1:2) → должен отклонить"""
        ok, msg, _, _ = check_rr(entry=100, stop=90, take=110, direction='long')
        self.assertFalse(ok, "Должен был отклонить плохой RR")
        self.assertIn("< 3", msg)

    def test_short_good_rr(self):
        """Short: хороший RR (1:4) → должен пройти"""
        ok, msg, risk, reward = check_rr(entry=100, stop=110, take=60, direction='short')
        self.assertTrue(ok, f"Ожидали OK, но получили: {msg}")
        self.assertGreaterEqual(reward / risk, 3.0)

    def test_short_bad_rr(self):
        """Short: плохой RR (1:2) → должен отклонить"""
        ok, msg, _, _ = check_rr(entry=100, stop=110, take=80, direction='short')
        self.assertFalse(ok, "Должен был отклонить плохой RR")
        self.assertIn("< 3", msg)

    def test_invalid_long_prices(self):
        """Long: Stop выше Entry → ошибка"""
        ok, msg, _, _ = check_rr(entry=100, stop=110, take=120, direction='long')
        self.assertFalse(ok)
        self.assertIn("НИЖЕ", msg)

    def test_invalid_short_prices(self):
        """Short: Stop ниже Entry → ошибка"""
        ok, msg, _, _ = check_rr(entry=100, stop=90, take=80, direction='short')
        self.assertFalse(ok)

if __name__ == '__main__':
    unittest.main(verbosity=2)   