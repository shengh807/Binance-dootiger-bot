import enum
from datetime import datetime as _datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Base
from .coin import Coin


class CoinPrice(Base):
    __tablename__ = "coin_price"

    coin = Column(String, primary_key=True)
    datetime = Column(DateTime, primary_key=True)
    interval = Column(String, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    def __init__(self, coin: Coin, datetime: str, interval: String, ohlcv: list):
        self.coin = coin
        self.datetime = datetime
        self.interval = interval
        self.open = ohlcv[1]
        self.high = ohlcv[2]
        self.low = ohlcv[3]
        self.close = ohlcv[4]
        self.volume = ohlcv[5]

    @hybrid_property
    def close_value(self):
        return self.close

    def info(self):
        return {
            "datetime": self.datetime.isoformat(),
            "coin_id": self.coin_id,
            "interval": self.interval,
            "close": self.close,
        }
