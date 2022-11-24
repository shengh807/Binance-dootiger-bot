import enum
from datetime import datetime as _datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class BacktestHistory(Base):
    __tablename__ = "backtest_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(String)
    datetime = Column(DateTime)
    trade_coin = Column(String)
    trade_coin_price = Column(Float)
    trade_coin_balance = Column(Float)
    total_coin_price = Column(Float)
    total_coin_balance = Column(Float)
    total_usdt = Column(Float)
    buy_more_cnt = Column(Integer)
    time_stamp = Column(DateTime)

    def __init__(
            self,
            strategy_id: str,
            datetime: str,
            trade_coin: str,
            trade_coin_price: float,
            trade_coin_balance: float,
            total_coin_price: float,
            total_coin_balance: float,
            total_usdt: float,
            buy_more_cnt: int,
    ):
        self.strategy_id = strategy_id
        self.datetime = datetime
        self.trade_coin = trade_coin
        self.trade_coin_price = trade_coin_price
        self.trade_coin_balance = trade_coin_balance
        self.total_coin_price = total_coin_price
        self.total_coin_balance = total_coin_balance
        self.total_usdt = total_usdt
        self.buy_more_cnt = buy_more_cnt

    def info(self):
        return {
            "id": self.id,
            "strategy_id": self.strategy_id,
            "datetime": self.datetime.isoformat(),
            "trade_coin": self.trade_coin,
            "trade_coin_price": self.trade_coin_price,
            "trade_coin_balance": self.trade_coin_balance,
            "total_coin_price": self.total_coin_price,
            "total_coin_balance": self.total_coin_balance,
            "total_usdt": self.current_usdt,
            "buy_more_cnt": self.buy_more_cnt,
        }
