

import sys
import json
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



def respond(ok: bool, data=None, error: str = ""):
    result = {"ok": ok, "data": data, "error": error}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if ok else 1)


def main():
    if len(sys.argv) < 2:
        respond(False, error="Не передана дія (action)")

    action = sys.argv[1].strip().lower()
    args = {}

    if len(sys.argv) >= 3:
        try:
            args = json.loads(sys.argv[2])
        except Exception as e:
            respond(False, error=f"Помилка парсингу JSON: {e}")

    # ── get_balance ────────────────────────────────────────────────
    if action == "get_balance":
        from parcer import BinanceAccount
        try:
            account = BinanceAccount()
            bal = account.get_usdt_balance()
            if bal:
                respond(True, data=bal)
            else:
                respond(False, error="Не вдалось отримати баланс")
        except Exception as e:
            respond(False, error=str(e))

    # ── calc_leverage ──────────────────────────────────────────────
    elif action == "calc_leverage":
        from parcer import BinanceAccount
        from leverage import RiskManager
        try:

            account = BinanceAccount()
            manager = RiskManager(account=account)
            lev = manager.calculate_leverage(
                entry=float(args["entry"]),
                stop=float(args["stop"]),
                risk_usd=float(args["risk_usd"]),
                risk_percent=float(args["risk_percent"])
            )
            respond(True, data={"leverage": lev})
        except Exception as e:
            respond(False, error=str(e))

    # ── open_trade ─────────────────────────────────────────────────
    elif action == "open_trade":
        from trader import Trader
        try:
            t = Trader()
            ok, msg = t.open_trade(
                pair=args["pair"],
                entry=float(args["entry"]),
                stop=float(args["stop"]),
                take=float(args["take"]),
                reason_entry=args.get("reason", ""),
                fear_greed=int(args.get("fear_greed", 50)),
                direction=args.get("direction", "long"),
                leverage=int(args.get("leverage", 1)),
                risk_dollar=float(args.get("risk_dollar", 0)),
                risk_percent=float(args.get("risk_percent", 1))
            )
            respond(ok, data={"message": msg})
        except Exception as e:
            respond(False, error=str(e))

    # ── close_trade ────────────────────────────────────────────────
    elif action == "close_trade":
        from trader import Trader
        try:
            t = Trader()
            ok, msg = t.close_trade(
                pair=args["pair"],
                reason_close=args.get("reason", "")
            )
            respond(ok, data={"message": msg})
        except Exception as e:
            respond(False, error=str(e))

    # ── get_positions ──────────────────────────────────────────────
    elif action == "get_positions":
        from trader import Trader
        try:
            t = Trader()
            positions = t.get_open_positions()
            respond(True, data={"positions": positions})
        except Exception as e:
            respond(False, error=str(e))

    # ── monitor ────────────────────────────────────────────────────
    elif action == "monitor":
        from trader import Trader
        try:
            t = Trader()
            info = t.monitor_trades()
            respond(True, data={"info": info})
        except Exception as e:
            respond(False, error=str(e))

    else:
        respond(False, error=f"Невідома дія: {action}")


if __name__ == "__main__":
    main()