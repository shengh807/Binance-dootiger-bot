import random
import sys
from datetime import datetime

from binance_dootiger_bot.common.auto_trader import AutoTrader


class Strategy(AutoTrader):     # AutoTrader 로 상속받아 생성된 전략파일
    def initialize(self):
        self.logger.debug("Strategy.initialize Called")
        super().initialize()    # AutoTrader.initialize() 실행. pair의 ratio 컬럼 셋팅
        self.initialize_current_coin()  # current_coin_history 테이블 셋팅

    def scout(self):
        """
        Scout for potential jumps from the current coin to another coin
        """
        self.logger.debug("Strategy.scout Called")
        self.logger.debug(self.manager.datetime)

        # current_coin_history 테이블 조회
        current_coin = self.db.get_current_coin()

        # Display on the console, the current coin+Bridge, so users can see *some* activity and not think the bot  has
        # stopped. Not logging though to reduce log size.
        print(
            f"{datetime.now()} - CONSOLE - INFO - I am scouting the best trades. "
            f"Current coin: {current_coin + self.config.BRIDGE} ",
            # end="\r",
        )
        self.logger.warning(f"{current_coin} {datetime.now()}")

        # 현재 가지고있는 코인 가격 조회
        current_coin_price = self.manager.get_ticker_price(current_coin + self.config.BRIDGE)

        if current_coin_price is None:
            self.logger.info("Skipping scouting... current coin {} not found".format(current_coin + self.config.BRIDGE))
            return

        # 코인종목[XRP], 코인가격[1.055] param
        # self._jump_to_best_coin(current_coin, current_coin_price)

    def bridge_scout(self):
        self.logger.debug("Strategy.bridge_scout Called")
        current_coin = self.db.get_current_coin()
        if self.manager.get_currency_balance(current_coin.symbol) > self.manager.get_min_notional(
            current_coin.symbol, self.config.BRIDGE.symbol
        ):
            # Only scout if we don't have enough of the current coin
            return
        new_coin = super().bridge_scout()
        if new_coin is not None:
            self.db.set_current_coin(new_coin)

    def initialize_current_coin(self):
        """
        Decide what is the current coin, and set it up in the DB.
        current_coin_history 테이블 셋팅
        """
        self.logger.debug("Strategy.initialize_current_coin Called")
        if self.db.get_current_coin() is None:
            current_coin_symbol = self.config.CURRENT_COIN_SYMBOL
            if not current_coin_symbol:
                current_coin_symbol = random.choice(self.config.SUPPORTED_COIN_LIST)

            self.logger.info(f"Setting initial coin to {current_coin_symbol}")

            if current_coin_symbol not in self.config.SUPPORTED_COIN_LIST:
                sys.exit("***\nERROR!\nSince there is no backup file, a proper coin name must be provided at init\n***")
            self.db.set_current_coin(current_coin_symbol)

            # if we don't have a configuration, we selected a coin at random... Buy it so we can start trading.
            if self.config.CURRENT_COIN_SYMBOL == "":
                current_coin = self.db.get_current_coin()
                self.logger.info(f"Purchasing {current_coin} to begin trading")
                self.manager.buy_alt(current_coin, self.config.BRIDGE)
                self.logger.info("Ready to start trading")
