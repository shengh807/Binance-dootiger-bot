import math
import time

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

from binance.exceptions import BinanceAPIException

from binance_dootiger_bot.service.binance_api_manager import BinanceAPIManager
from binance_dootiger_bot.service.binance_stream_manager import BinanceOrder, BinanceStreamManager
from binance_dootiger_bot.common.config import Config
from binance_dootiger_bot.service.database_manager import Database
from binance_dootiger_bot.common.logger import Logger
from binance_dootiger_bot.models import Coin, CoinPrice

from binance.enums import HistoricalKlinesType


class MockBinanceManager(BinanceAPIManager):
    def __init__(
        self,
        config: Config,
        db: Database,
        logger: Logger,
        start_date: datetime = None,
    ):
        super().__init__(config, db, logger)
        # self.config = config
        self.datetime = start_date  # Backtest 할때만 사용함
        self.balances = {}
        self.backtest_yn = False

    # def setup_websockets(self):
    #     pass  # No websockets are needed for backtesting

    def increment(self, interval=1):
        self.datetime += timedelta(minutes=interval)

    def get_fee(self, origin_coin: Coin, target_coin: Coin, selling: bool):
        return 0.0001  # 0.1%

    def get_ticker_price(self, ticker_symbol: str):
        """
        Get ticker price of a specific coin
        """
        interval = "5m"
        return_price = 0

        if self.backtest_yn == False:
            self.datetime = datetime.now()
        target_date = self.datetime - timedelta(minutes=5) - timedelta(minutes=int(self.datetime.strftime("%M")) % 5)
        target_date_reset = datetime(target_date.year, target_date.month, target_date.day,
                                     target_date.hour, target_date.minute)

        target_date_kr = target_date_reset.strftime("%Y-%m-%d %H:%M:%S")
        coin_price = self.db.get_coin_price(ticker_symbol, target_date_kr, interval,)

        # DB 값이 없을 때 재조회
        if coin_price is None:
            self.set_ticker_price(ticker_symbol, target_date)
            coin_price = self.db.get_coin_price(ticker_symbol, target_date_kr, interval, )

        # DB값 셋팅 후에도 없을 때 Stream 값으로 조회 후 저장
        if coin_price is not None:
            return_price = coin_price.close
        else:
            self.logger.warning("★★get_ticker_price Cache Stream selected★★")
            return_price = super().get_ticker_price(ticker_symbol)

        return return_price

    def set_ticker_price(self, ticker_symbol: str, td: datetime = None):
        """
        Get ticker price of a specific coin
        """
        if td is None:
            td = datetime.now()

        td = td - timedelta(hours=9) - timedelta(minutes=int(td.strftime("%M")) % 5)
        print(td)

        td = td.replace(second=0)
        end_date = td + timedelta(minutes=1000)
        end_date = end_date.strftime("%d %b %Y %H:%M:%S")

        # 1분봉 Update
        # self.get_data_from_api_to_db(ticker_symbol, td, end_date, "1m")

        # 5분봉 Update
        if td.minute % 5 == 0:
            self.get_data_from_api_to_db(ticker_symbol, td, end_date, "5m")

        # 15분봉 Update
        if td.minute % 15 == 0:
            self.get_data_from_api_to_db(ticker_symbol, td, end_date, "15m")

        # 30분봉 Update
        if td.minute % 30 == 0:
            self.get_data_from_api_to_db(ticker_symbol, td, end_date, "30m")

        print(ticker_symbol + " " + td.strftime("%d %b %Y %H:%M:%S") + " insert Done!!!!!")

    def get_data_from_api_to_db(self, ticker_symbol: str, td: datetime = None, ed: str = None, interval: str = "1m", ):
        if interval == "5m":
            td = td - timedelta(minutes=5)
        elif interval == "15m":
            td = td - timedelta(minutes=15)
        elif interval == "30m":
            td = td - timedelta(minutes=30)

        target_date_kr = td + timedelta(hours=9)
        target_date_kr = target_date_kr.strftime("%Y-%m-%d %H:%M:%S")

        coin_price = self.db.get_coin_price(ticker_symbol, target_date_kr, interval,)
        if coin_price is None:
            target_date = td - timedelta(hours=1)
            target_date = target_date.strftime("%d %b %Y %H:%M:%S")
            self.get_historical_klines_to_db(ticker_symbol, target_date, ed, interval,)

    def get_historical_klines_to_db(self, ticker_symbol, target_date, end_date, interval: str):
        """
        Get historical klines and update table
        """
        result_list = self.binance_client.get_historical_klines(
            ticker_symbol, interval, target_date, end_date, limit=1000, klines_type=HistoricalKlinesType.FUTURES,
        )

        for result in result_list[:len(result_list) - 1]:
            date1 = datetime.utcfromtimestamp(result[0] / 1000) + timedelta(hours=9)
            date1 = date1.strftime("%Y-%m-%d %H:%M:%S")

            try:
                if self.db.get_coin_price(ticker_symbol, date1, interval, ) is None:
                    self.db.set_coin_price(ticker_symbol, date1, interval, result)
                    # self.logger.warning(f"[{ticker_symbol}] {date1} {interval}")
            except Exception as e:
                self.logger.info(f"Unexpected Error: {e}")
                # self.db.update_coin_price(ticker_symbol, date1, interval, result)

            print("api date: " + target_date + " :::::::::::: real date: " + date1)

    def get_historical_klines_realtime(self, ticker_symbol: str, interval: str = "1m", ):
        """
        Get historical klines realtime
        """
        td = datetime.now() - timedelta(hours=9)

        target_date = td - timedelta(hours=1)
        target_date = target_date.strftime("%d %b %Y %H:%M:%S")

        end_date = td + timedelta(minutes=1000)
        end_date = end_date.strftime("%d %b %Y %H:%M:%S")

        result_list = self.binance_client.get_historical_klines(
            ticker_symbol, interval, target_date, end_date, limit=1000, klines_type=HistoricalKlinesType.FUTURES,
        )
        result_list.reverse()
        print(f"get_historical_klines 에서 가지고 온 값..\n{result_list[0]}")

        coin_price = CoinPrice(ticker_symbol, td, interval, result_list[0])

        return coin_price

    def get_currency_balance(self, strategy_name: str, currency_symbol: str, force=False):
        """
        Get balance of a specific coin
        """
        return self.balances[strategy_name].get(currency_symbol, 0)

    def buy_alt(self, strategy_name: str, origin_coin: Coin, target_coin: Coin, target_balance: float, coin_price: float = None):
        origin_symbol = origin_coin.symbol
        target_symbol = target_coin.symbol
        target_balance = target_balance

        # 거래 데이터 계산
        from_coin_price = self.get_ticker_price(origin_symbol + target_symbol)  # BTCUSDT 가격 조회
        # 2022.02.18 입력받은 매수가가 있으면 매도가격 변경
        if coin_price is not None:
            from_coin_price = coin_price
        order_quantity = self.buy_quantity(origin_symbol, target_symbol, target_balance, from_coin_price)  # 코인 거래 갯수 셋팅
        target_quantity = order_quantity * from_coin_price  # 거래에 필요한 target(USDT) 갯수 셋팅

        # 실제 거래 수행
        if self.backtest_yn == False:
            print("Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ ")
            self.logger.debug("BinanceAPIManager.buy_alt Called")
            if order_quantity > 0:
                self.retry(self._buy_alt, origin_coin, target_coin, order_quantity, from_coin_price)
            else:
                self.retry(self._sell_alt, origin_coin, target_coin, -order_quantity, from_coin_price)

        # 잔고 balances Dict 에 Update
        # BTC_price : 평단가
        self.balances[strategy_name][origin_symbol+"_price"] = (self.balances[strategy_name].get(origin_symbol+"_price", 0) * self.balances[strategy_name].get(origin_symbol, 0) \
                                                + from_coin_price * order_quantity * (1 - self.get_fee(origin_coin, target_coin, False))) \
                                                / (self.balances[strategy_name].get(origin_symbol, 0) + order_quantity * (1 - self.get_fee(origin_coin, target_coin, False)))

        # USDT : 이번 거래에 사용된 USDT
        self.balances[strategy_name][target_symbol] = target_quantity

        # BTC : BTC 총 소지갯수
        self.balances[strategy_name][origin_symbol] = round(self.balances[strategy_name][origin_symbol] + order_quantity, 3)

        # USDT_total : USDT 총 소지금액 (거래수수료 차감 포함된 금액)
        self.balances[strategy_name][target_symbol+"_total"] -= target_quantity + order_quantity * (1 - self.get_fee(origin_coin, target_coin, False))

        self.logger.info(
            f"Bought {origin_symbol}, total balance : {self.balances[strategy_name][origin_symbol]}"
        )

        ## backtest_history DB Insert
        self.db.set_backtest_history(
                strategy_name,
                self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                origin_symbol + target_symbol,  # USDT + BTC
                from_coin_price,
                order_quantity,
                self.balances[strategy_name][origin_symbol+"_price"],
                self.balances[strategy_name][origin_symbol],
                self.balances[strategy_name][target_symbol+"_total"],
                self.balances[strategy_name]['buy_more_cnt'])

        return True

    def buy_quantity(
        self, origin_symbol: str, target_symbol: str, target_balance: float = None, from_coin_price: float = None
    ):
        # self.manager.datetime OPEN 시점에 target_balance로 살수 있는 갯수 조회
        # if self.backtest_yn == True:
        result_quantity = math.floor(target_balance * (10 ** 3) / from_coin_price) / float(10 ** 3)
        # else:
        #     result_quantity = self._buy_quantity(origin_symbol, target_symbol, target_balance, from_coin_price)

        return result_quantity

    def sell_alt(self, strategy_name: str, origin_coin: Coin, target_coin: Coin, per: int, coin_price: float = None):
        origin_symbol = origin_coin.symbol
        target_symbol = target_coin.symbol

        # 거래 데이터 계산
        from_coin_price = self.get_ticker_price(origin_symbol + target_symbol)  # BTCUSDT 가격 조회
        # 2022.02.18 입력받은 매도가가 있으면 매도가격 변경
        if coin_price is not None:
            from_coin_price = coin_price
        origin_balance = self.get_currency_balance(strategy_name, origin_symbol) * per / 100  # 코인 거래 갯수 셋팅
        # order_quantity = origin_balance
        
        # 2022.01.16 전량매도 시 갯수(0.013000000000000001) 로 가지고오는 오류 건 수정
        # if per != 100:  # 전량매도가 아닐 시 거래가능한 갯수로 셋팅 (0.001)
        order_quantity = self.sell_quantity(origin_symbol, target_symbol, origin_balance)
        
        target_quantity = order_quantity * from_coin_price  # 거래에 필요한 target(USDT) 갯수 셋팅

        # 실제 거래 수행
        if self.backtest_yn == False:
            print("Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ Real Trade @@ ")
            self.logger.debug("BinanceAPIManager.buy_alt Called")
            if order_quantity > 0:
                self.retry(self._sell_alt, origin_coin, target_coin, order_quantity, from_coin_price)
            else:
                self.retry(self._buy_alt, origin_coin, target_coin, -order_quantity, from_coin_price)

        # 잔고 balances Dict 에 Update
        # BTC : BTC 총 소지갯수
        self.balances[strategy_name][origin_symbol] = round(self.balances[strategy_name][origin_symbol] - order_quantity, 3)

        # USDT_total : USDT 총 소지금액 (거래수수료 차감 포함된 금액)
        self.balances[strategy_name][target_symbol+"_total"] = self.balances[strategy_name].get(target_symbol+"_total", 0) + target_quantity * (1 - self.get_fee(origin_coin, target_coin, True))

        self.logger.info(
            f"Sold {origin_symbol}, total balance : {self.balances[strategy_name][origin_symbol]}"
        )

        # balances 보정작업
        if - 0.0001 < self.balances[strategy_name][origin_symbol] < 0.0001:
            self.balances[strategy_name][origin_symbol] = 0

        if self.balances[strategy_name][origin_symbol] == 0:
            self.balances[strategy_name][origin_symbol + "_price"] = 0

        ## DB Insert
        self.db.set_backtest_history(
                strategy_name,
                self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                origin_symbol + target_symbol,  # USDT + BTC
                from_coin_price,
                - order_quantity,
                self.balances[strategy_name][origin_symbol+"_price"],
                self.balances[strategy_name][origin_symbol],
                self.balances[strategy_name][target_symbol+"_total"],
                self.balances[strategy_name]['buy_more_cnt'])

        return True

    def sell_quantity(self, origin_symbol: str, target_symbol: str, origin_balance: float = None):
        self.logger.debug("BinanceAPIManager.sell_quantity Called")

        # if self.backtest_yn == True:
        result_quantity = math.floor(origin_balance * 10 ** 3) / float(10 ** 3)
        # else:
        #     result_quantity = self._sell_quantity(origin_symbol, target_symbol, origin_balance)

        return result_quantity

class MockDatabase(Database):
    def __init__(self, config: Config):
        super().__init__(config, )

