import time
from datetime import datetime
from traceback import format_exc
from typing import Dict
from binance_dootiger_bot.common.config import Config
from binance_dootiger_bot.common.logger import Logger
from .strategies import get_strategy
from binance_dootiger_bot.service.binance_doobot_manager import MockDatabase, MockBinanceManager


class Backtest:
    def __init__(self, config: Config = None,):
        self.config = config or Config()
        self.db = MockDatabase(self.config)
        self.logger = Logger("backtesting", self.db)

    def backtest(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        interval=5,
        yield_interval=100,
        start_balances: Dict[str, float] = None,
        starting_coin: str = None
    ):
        """
        :param config: Configuration object to use
        :param start_date: Date to  backtest from
        :param end_date: Date to backtest up to
        :param interval: Number of virtual minutes between each scout
        :param yield_interval: After how many intervals should the manager be yielded
        :param start_balances: A dictionary of initial coin values. Default: {BRIDGE: 100}
        :param starting_coin: The coin to start on. Default: first coin in coin list

        :return: The final coin balances
        """

        end_date = end_date or datetime.today()

        self.db.create_database()
        manager = MockBinanceManager(self.config, self.db, self.logger, start_date, )
        manager.backtest_yn = True

        strategy_nm = "doobotx02"
        strategy = get_strategy(strategy_nm)
        if strategy is None:
            self.logger.error("Invalid strategy name")
            return manager
        trader = strategy(manager, self.db, self.logger, self.config )
        trader.initialize()

        yield manager

        n = 1
        try:
            while manager.datetime < end_date:
                try:
                    trader.scout()
                    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!{manager.datetime} / {end_date} 백테스트 완료!!!!!!!!!!!!!!!!!!!!!!")
                except Exception:  # pylint: disable=broad-except
                    self.logger.warning(format_exc())
                manager.increment(interval)
                if n % yield_interval == 0:
                    yield manager
                n += 1
                # time.sleep(0.02)
        except KeyboardInterrupt:
            pass
        # cache.close()
        return manager
