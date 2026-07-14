import pandas as pd
from datetime import datetime
import os
from abc import ABC, abstractmethod


COLUMNS = [
    'id',
    'pair',
    'direction',
    'entry_price',
    'stop_loss',
    'take_profit',
    'leverage',
    'rr_ratio',
    'reason_entry',
    'reason_close',
    'potential_profit',
    'potential_loss',
    'pnl',
    'trade_time',
    'fear_greed',
    'profit_shans',
    'tradingview_link',
    'why_lose'
]


class BaseJournal(ABC):

    def __init__(self, file_name: str):
        self._file_name = file_name

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def save(self, df):
        pass


class ExcelTradeJournal(BaseJournal):

    def __init__(self, file_name='trade_journal.xlsx'):
        super().__init__(file_name) #вызываем __init__ из BaseJournal и берём с него file_name
        self.__init_journal()

    def __init_journal(self):

        if not os.path.exists(self._file_name):
            df = pd.DataFrame(columns=COLUMNS)
            df.to_excel(self._file_name, index=False)

    def __load(self):
        return pd.read_excel(self._file_name)

    def __save(self, df):
        df.to_excel(self._file_name, index=False)

    def load(self):
        return self.__load()

    def save(self, df):
        self.__save(df)


    def insert_open_trade(self, data: dict):

        df = self.__load()

        data['id'] = len(df) + 1
        data['trade_time'] = (
            f"open: {datetime.now().isoformat()}, close: None"
        )

        data['pnl'] = None
        data['reason_close'] = None
        data['why_lose'] = None
        data['tradingview_link'] = data.get(
            'tradingview_link'
        )

        new_row = pd.DataFrame([data])

        df = pd.concat(
            [df, new_row],
            ignore_index=True
        )

        self.__save(df)

        return data['id']

    def close_trade(self, pair: str, pnl: float, reason_close: str = None):

        df = self.__load()

        open_mask = (
            (df['pair'] == pair)
            &
            (df['pnl'].isna())
        )

        indexes = df[open_mask].index

        if len(indexes) == 0:
            return False

        idx = indexes[-1]

        now = datetime.now().isoformat()

        current_time = str(
            df.loc[idx, 'trade_time']
        )

        if "close: None" in current_time:

            new_time = current_time.replace(
                "close: None",
                f"close: {now}"
            )

        else:

            new_time = (
                f"{current_time}, close: {now}"
            )

        df.loc[idx, 'trade_time'] = new_time
        df.loc[idx, 'pnl'] = pnl
        df.loc[idx, 'reason_close'] = reason_close

        self.__save(df)

        return True

    def get_open_positions(self):

        df = self.__load()

        open_df = df[
            df['pnl'].isna()
        ]

        positions = []

        for _, row in open_df.iterrows():

            positions.append(
                f"{row['pair']} "
                f"({row['direction']}) "
                f"ID:{int(row['id'])}"
            )

        return positions

    def get_all_trades(self):
        return self.__load()





# import pandas as pd
# from datetime import datetime
# import os

# DB_FILE = 'trade_journal.xlsx'

# COLUMNS = [
#     'id', 'pair', 'direction', 'entry_price', 'stop_loss', 'take_profit',
#     'leverage', 'rr_ratio', 'reason_entry', 'reason_close',
#     'potential_profit', 'potential_loss', 'pnl',
#     'trade_time', 'fear_greed', 'profit_shans', 'tradingview_link', 'why_lose'
# ]

# def init_journal():
#     """Создаёт Excel-файл с нужными колонками"""
#     if not os.path.exists(DB_FILE):
#         pd.DataFrame(columns=COLUMNS).to_excel(DB_FILE, index=False)


# def insert_open_trade(data: dict):
#     """Сохраняет сделку в Excel (без скриншотов, только TradingView ссылка)"""
#     init_journal()
#     df = pd.read_excel(DB_FILE)

#     data['id'] = len(df) + 1
#     data['trade_time'] = f"open: {datetime.now().isoformat()}, close: None"
#     data['pnl'] = None
#     data['reason_close'] = None
#     data['why_lose'] = None
#     data['tradingview_link'] = data.get('tradingview_link', None)

#     new_row = pd.DataFrame([data])
#     df = pd.concat([df, new_row], ignore_index=True)
#     df.to_excel(DB_FILE, index=False)
#     return data['id']


# def close_trade(pair: str, pnl: float, reason_close: str = None):
#     """Закрытие позиции по паре"""
#     df = pd.read_excel(DB_FILE)
    
#     open_mask = (df['pair'] == pair) & (df['pnl'].isna())
#     idx = df[open_mask].index
    
#     if len(idx) == 0:
#         return False
    
#     idx_to_update = idx[-1]  # последняя открытая
    
#     now = datetime.now().isoformat()
#     current_time = str(df.loc[idx_to_update, 'trade_time'])
    
#     if "close: None" in current_time:
#         new_time = current_time.replace("close: None", f"close: {now}")
#     else:
#         new_time = f"{current_time}, close: {now}"
    
#     df.loc[idx_to_update, 'trade_time'] = new_time
#     df.loc[idx_to_update, 'pnl'] = pnl
#     df.loc[idx_to_update, 'reason_close'] = reason_close
#     df.to_excel(DB_FILE, index=False)
    
#     return True


# def get_open_positions():
#     """Для меню закрытия"""
#     df = pd.read_excel(DB_FILE)
#     open_df = df[df['pnl'].isna()]
#     return [f"{row['pair']} ({row['direction']}) ID:{int(row['id'])}" 
#             for _, row in open_df.iterrows()]