import pandas as pd
from datetime import datetime
import os

DB_FILE = 'trade_journal.xlsx'

COLUMNS = [
    'id', 'pair', 'direction', 'entry_price', 'stop_loss', 'take_profit',
    'leverage', 'rr_ratio', 'reason_entry', 'reason_close',
    'potential_profit', 'potential_loss', 'pnl',
    'trade_time', 'fear_greed', 'profit_shans', 'tradingview_link', 'why_lose'
]

def init_journal():
    """Создаёт Excel-файл с нужными колонками"""
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=COLUMNS).to_excel(DB_FILE, index=False)


def insert_open_trade(data: dict):
    """Сохраняет сделку в Excel (без скриншотов, только TradingView ссылка)"""
    init_journal()
    df = pd.read_excel(DB_FILE)

    data['id'] = len(df) + 1
    data['trade_time'] = f"open: {datetime.now().isoformat()}, close: None"
    data['pnl'] = None
    data['reason_close'] = None
    data['why_lose'] = None
    data['tradingview_link'] = data.get('tradingview_link', None)

    new_row = pd.DataFrame([data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(DB_FILE, index=False)
    return data['id']


def close_trade(pair: str, pnl: float, reason_close: str = None):
    """Закрытие позиции по паре"""
    df = pd.read_excel(DB_FILE)
    
    open_mask = (df['pair'] == pair) & (df['pnl'].isna())
    idx = df[open_mask].index
    
    if len(idx) == 0:
        return False
    
    idx_to_update = idx[-1]  # последняя открытая
    
    now = datetime.now().isoformat()
    current_time = str(df.loc[idx_to_update, 'trade_time'])
    
    if "close: None" in current_time:
        new_time = current_time.replace("close: None", f"close: {now}")
    else:
        new_time = f"{current_time}, close: {now}"
    
    df.loc[idx_to_update, 'trade_time'] = new_time
    df.loc[idx_to_update, 'pnl'] = pnl
    df.loc[idx_to_update, 'reason_close'] = reason_close
    df.to_excel(DB_FILE, index=False)
    
    return True


def get_open_positions():
    """Для меню закрытия"""
    df = pd.read_excel(DB_FILE)
    open_df = df[df['pnl'].isna()]
    return [f"{row['pair']} ({row['direction']}) ID:{int(row['id'])}" 
            for _, row in open_df.iterrows()]