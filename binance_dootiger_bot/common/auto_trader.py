from datetime import datetime
from typing import Dict, List

from sqlalchemy.orm import Session

from binance_dootiger_bot.service.binance_api_manager import BinanceAPIManager
from binance_dootiger_bot.common.config import Config
from binance_dootiger_bot.service.database_manager import Database
from binance_dootiger_bot.common.logger import Logger
from binance_dootiger_bot.models import Coin, CoinValue


class AutoTrader:
    def __init__(self, binance_manager: BinanceAPIManager, database: Database, logger: Logger, config: Config ):
        self.manager = binance_manager
        self.db = database
        self.logger = logger
        self.config = config

        self.logger.debug("AutoTrader.__init__ Called")

    def initialize(self):
        self.logger.debug("AutoTrader.initialize Called")
        self.initialize_trade_thresholds()

    def initialize_trade_thresholds(self):

        account = self.db.get_backtest_history(self.strategy_name, self.config.SUPPORTED_COIN_LIST[0])
        balances = {}  # 초기값 셋팅

        if account is not None:
            balances[self.config.BRIDGE.symbol+"_total"] = account.total_usdt
            balances[self.config.SUPPORTED_COIN_LIST[0]] = account.total_coin_balance
            balances[self.config.SUPPORTED_COIN_LIST[0]+"_price"] = account.total_coin_price
            balances[self.config.BRIDGE.symbol] = 0
            balances["buy_more_cnt"] = account.buy_more_cnt
            balances["sell_more_cnt"] = 0

        else:
            balances[self.config.BRIDGE.symbol+"_total"] = float(self.BACKTEST_START_USDT_BALANCE)
            balances[self.config.SUPPORTED_COIN_LIST[0]] = 0
            balances[self.config.SUPPORTED_COIN_LIST[0]+"_price"] = 0
            balances[self.config.BRIDGE.symbol] = 0
            balances["buy_more_cnt"] = 0
            balances["sell_more_cnt"] = 0

            if self.manager.backtest_yn == True:
                dt = self.manager.datetime.strftime("%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

            ## DB Insert
            self.db.set_backtest_history(
                self.strategy_name,
                dt,
                self.config.SUPPORTED_COIN_LIST[0] + self.config.BRIDGE.symbol,  # USDT + BTC
                0,
                0,
                balances[self.config.SUPPORTED_COIN_LIST[0] + "_price"],
                balances[self.config.SUPPORTED_COIN_LIST[0]],
                balances[self.config.BRIDGE.symbol + "_total"],
                balances["buy_more_cnt"])

        self.manager.balances[self.strategy_name] = balances



    def scout(self):
        """
        Scout for potential jumps from the current coin to another coin
        """
        raise NotImplementedError()

    def buy_coin(self, coin: Coin):
        raise NotImplementedError()

    def buy_more_coin(self, coin: Coin):
        raise NotImplementedError()

    def cell_coin(self, coin: Coin):
        raise NotImplementedError()
