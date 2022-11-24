import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Union

from socketio import Client
from socketio.exceptions import ConnectionError as SocketIOConnectionError
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from binance_dootiger_bot.common.config import Config
from binance_dootiger_bot.models import *  # pylint: disable=wildcard-import


class Database:
    def __init__(self, config: Config, uri="sqlite:///data/crypto_trading.db"):
        self.config = config
        # self.engine = create_engine(uri)
        self.engine = create_engine("mysql+mysqldb://root:" + "Dkagh01!" + "@localhost/binance?charset=utf8"
                                    , encoding='utf-8', pool_size=150, max_overflow=0, pool_recycle=500)
        self.SessionMaker = sessionmaker(bind=self.engine)
        self.socketio_client = Client()

    def socketio_connect(self):
        if self.socketio_client.connected and self.socketio_client.namespaces:
            return True
        try:
            if not self.socketio_client.connected:
                self.socketio_client.connect("http://api:5123", namespaces=["/backend"])
            while not self.socketio_client.connected or not self.socketio_client.namespaces:
                time.sleep(0.1)
            return True
        except SocketIOConnectionError:
            return False

    @contextmanager
    def db_session(self):
        """
        Creates a context with an open SQLAlchemy session.
        """
        session: Session = scoped_session(self.SessionMaker)
        yield session
        session.commit()
        session.close()

    def get_coin_price(self, coin: Union[Coin, str], datetime: str, interval: str, ) -> CoinPrice:
        print("select * from coin_price where ", coin, datetime, interval)

        session: Session
        with self.db_session() as session:
            coin_price = session.query(CoinPrice).filter(CoinPrice.coin == coin, CoinPrice.datetime == datetime,
                                                         CoinPrice.interval == interval).first()
            session.expunge_all()
            return coin_price

    def get_coin_price_list(self, coin: Union[Coin, str], interval: str, datetime: str, limit: int = 3) -> List[
        CoinPrice]:

        session: Session
        with self.db_session() as session:
            if datetime is None:
                coin_price_list = session.query(CoinPrice).filter(CoinPrice.coin == coin,
                                                                  CoinPrice.interval == interval).order_by(
                    CoinPrice.datetime.desc()).limit(limit)
            else:
                coin_price_list = session.query(CoinPrice).filter(CoinPrice.coin == coin,
                                                                  CoinPrice.interval == interval,
                                                                  CoinPrice.datetime <= datetime
                                                                  ).order_by(CoinPrice.datetime.desc()).limit(limit)

            session.expunge_all()
            return coin_price_list

    def set_coin_price(self, coin: Union[Coin, str], datetime: str, interval: str, ohlcv: List[float]):
        """
        coin_price 테이블 데이터 Insert
        """
        print("insert coin_price into ", coin, datetime, interval)

        with self.db_session() as session:
            cc = CoinPrice(coin, datetime, interval, ohlcv)
            session.add(cc)

    def update_coin_price(self, coin: Union[Coin, str], datetime: str, interval: str, ohlcv: List[float]):
        """
        coin_price 테이블 데이터 Update
        """
        with self.db_session() as session:
            cc = CoinPrice(coin, datetime, interval, ohlcv)
            session.merge(cc)
            self.send_update(cc)

    ## 2021.12.27 Telegram History 추가
    def set_message_history(self, message: str):
        """
        message_history 테이블 데이터 Insert
        """
        print("insert message_history into ", message)

        with self.db_session() as session:
            cc = MessageHistory(message)
            session.add(cc)

    def get_message_history(self, datetime: str = None, message: str = None, ) -> CoinPrice:
        print("select * from message_history where ", datetime, message)

        if datetime is None:
            datetime = datetime.now()

        datetime = datetime.strftime("%Y-%m-%d %H")  # "%Y%m%d %H%M%S"

        session: Session
        with self.db_session() as session:
            message_history = session.query(MessageHistory).filter(MessageHistory.datetime.like(datetime + '%')
                                                                   , MessageHistory.message == message).first()
            session.expunge_all()
            return message_history

    ## 2021.12.30 Backtest History 추가
    def set_backtest_history(
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
        """
        backtest_history 테이블 데이터 Insert
        """
        print("insert backtest_history into ", strategy_id, datetime, total_usdt)

        with self.db_session() as session:
            cc = BacktestHistory(strategy_id, datetime, trade_coin, trade_coin_price, trade_coin_balance,
                                 total_coin_price, total_coin_balance, total_usdt, buy_more_cnt)
            session.add(cc)

    def get_backtest_history(self, strategy_id: str, coin: Union[Coin, str]):
        trade_coin = coin + self.config.BRIDGE.symbol

        session: Session
        with self.db_session() as session:
            backtest_history: BacktestHistory = session.query(BacktestHistory).filter(
                BacktestHistory.strategy_id == strategy_id,
                BacktestHistory.trade_coin == trade_coin
            ).order_by(BacktestHistory.datetime.desc()).first()
            if backtest_history is None:
                return None
            session.expunge(backtest_history)
            return backtest_history

    def get_common_code(self, code_id: str, value_id: str, ) -> CommonCode:
        print("select * from common_code where ", code_id, value_id)

        session: Session
        with self.db_session() as session:
            code = session.query(CommonCode).filter(CommonCode.code_id == code_id,
                                                    CommonCode.value_id == value_id).first()
            session.expunge_all()
            return code

    def get_score_value(self, stratgy_id: str, trans_gb_cd: str, score_st_cd: str, score: float) -> ScoreValue:
        print("select * from score_value where ", stratgy_id, trans_gb_cd, score_st_cd, str(score))
        return_score = 0

        session: Session
        with self.db_session() as session:
            score_value = session.query(ScoreValue).filter(ScoreValue.stratgy_id == stratgy_id,
                                                           ScoreValue.trans_gb_cd == trans_gb_cd,
                                                           ScoreValue.score_st_cd == score_st_cd,
                                                           ScoreValue.down_st_val <= score,
                                                           ScoreValue.up_st_val > score
                                                           ).first()
            session.expunge_all()

            if score_value is not None:
                return_score = score_value.st_score

            return return_score

    def get_coins(self, only_enabled=True) -> List[Coin]:
        session: Session
        with self.db_session() as session:
            if only_enabled:
                coins = session.query(Coin).filter(Coin.enabled).all()
            else:
                coins = session.query(Coin).all()
            session.expunge_all()
            return coins

    def get_coin(self, coin: Union[Coin, str]) -> Coin:
        if isinstance(coin, Coin):
            return coin
        session: Session
        with self.db_session() as session:
            coin = session.query(Coin).get(coin)
            session.expunge(coin)
            return coin

    def set_current_coin(self, coin: Union[Coin, str]):
        coin = self.get_coin(coin)
        session: Session
        with self.db_session() as session:
            if isinstance(coin, Coin):
                coin = session.merge(coin)
            cc = CurrentCoin(coin)
            session.add(cc)
            self.send_update(cc)

    def get_current_coin(self) -> Optional[Coin]:
        session: Session
        with self.db_session() as session:
            current_coin = session.query(CurrentCoin).order_by(CurrentCoin.datetime.desc()).first()
            if current_coin is None:
                return None
            coin = current_coin.coin
            session.expunge(coin)
            return coin

    def prune_value_history(self):
        session: Session
        with self.db_session() as session:
            # Sets the first entry for each coin for each hour as 'hourly'
            hourly_entries: List[CoinValue] = (
                session.query(CoinValue).group_by(CoinValue.coin_id, func.strftime("%H", CoinValue.datetime)).all()
            )
            for entry in hourly_entries:
                entry.interval = Interval.HOURLY

            # Sets the first entry for each coin for each day as 'daily'
            daily_entries: List[CoinValue] = (
                session.query(CoinValue).group_by(CoinValue.coin_id, func.date(CoinValue.datetime)).all()
            )
            for entry in daily_entries:
                entry.interval = Interval.DAILY

            # Sets the first entry for each coin for each month as 'weekly'
            # (Sunday is the start of the week)
            weekly_entries: List[CoinValue] = (
                session.query(CoinValue).group_by(CoinValue.coin_id, func.strftime("%Y-%W", CoinValue.datetime)).all()
            )
            for entry in weekly_entries:
                entry.interval = Interval.WEEKLY

            # The last 24 hours worth of minutely entries will be kept, so
            # count(coins) * 1440 entries
            time_diff = datetime.now() - timedelta(hours=24)
            session.query(CoinValue).filter(
                CoinValue.interval == Interval.MINUTELY, CoinValue.datetime < time_diff
            ).delete()

            # The last 28 days worth of hourly entries will be kept, so count(coins) * 672 entries
            time_diff = datetime.now() - timedelta(days=28)
            session.query(CoinValue).filter(
                CoinValue.interval == Interval.HOURLY, CoinValue.datetime < time_diff
            ).delete()

            # The last years worth of daily entries will be kept, so count(coins) * 365 entries
            time_diff = datetime.now() - timedelta(days=365)
            session.query(CoinValue).filter(
                CoinValue.interval == Interval.DAILY, CoinValue.datetime < time_diff
            ).delete()

            # All weekly entries will be kept forever

    def create_database(self):
        Base.metadata.create_all(self.engine)

    def send_update(self, model):
        if not self.socketio_connect():
            return

        self.socketio_client.emit(
            "update",
            {"table": model.__tablename__, "data": model.info()},
            namespace="/backend",
        )

    def migrate_old_state(self):
        """
        For migrating from old dotfile format to SQL db. This method should be removed in
        the future.
        """
        if os.path.isfile(".current_coin"):
            with open(".current_coin") as f:
                coin = f.read().strip()
                self.set_current_coin(coin)
            os.rename(".current_coin", ".current_coin.old")

        if os.path.isfile(".current_coin_table"):
            with open(".current_coin_table") as f:
                table: dict = json.load(f)
                session: Session
                with self.db_session() as session:
                    for from_coin, to_coin_dict in table.items():
                        for to_coin, ratio in to_coin_dict.items():
                            if from_coin == to_coin:
                                continue
                            pair = session.merge(self.get_pair(from_coin, to_coin))
                            pair.ratio = ratio
                            session.add(pair)

            os.rename(".current_coin_table", ".current_coin_table.old")


if __name__ == "__main__":
    print("TradeLog.__main__")
    database = Database(Config())
    database.create_database()
