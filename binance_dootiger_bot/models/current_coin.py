from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base
from .coin import Coin


class CurrentCoin(Base):  # pylint: disable=too-few-public-methods
    __tablename__ = "current_coin_history"
    id = Column(Integer, primary_key=True)
    coin_id = Column(String, ForeignKey("coins.symbol"))
    coin = relationship("Coin")
    datetime = Column(DateTime)

    def __init__(self, coin: Coin):
        print("models.CurrentCoin.__init__ Called")
        self.coin = coin
        # self.datetime = datetime.utcnow()
        self.datetime = datetime.now()

    def info(self):
        print("models.CurrentCoin.info Called")
        return {"datetime": self.datetime.isoformat(), "coin": self.coin.info()}
