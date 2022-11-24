import time
from datetime import datetime, timedelta
from binance_dootiger_bot.common.config import Config
from binance_dootiger_bot.common.logger import Logger
from binance_dootiger_bot.common.common_util import CommonUtil
from .strategies import get_strategy
from binance_dootiger_bot.service.binance_doobot_manager import MockDatabase, MockBinanceManager

from binance_dootiger_bot.common.scheduler import SafeScheduler


class DoobotTrading:
    def __init__(self, config: Config = None,):
        self.config = config or Config()
        self.db = MockDatabase(self.config)
        self.logger = Logger("doobot_trading", self.db)
        self.manager = MockBinanceManager(self.config, self.db, self.logger,)

    def update_coin_data_history(self, start_date: datetime = None, end_date: datetime = None,):
        for coin in self.config.SUPPORTED_COIN_LIST:
            loop_date = start_date
            while True:
            ## 1분봉 데이터 Insert - 가격조회하여 실시간으로 가지고옴
                self.manager.set_ticker_price(coin + self.config.BRIDGE.symbol, loop_date)
                if loop_date >= end_date - timedelta(minutes=1):  # 마지막으로 완성된 1분 전 봉 값만 적용
                    print("break!!!!!!!!!!")
                    break
                time.sleep(0.01)
                loop_date = loop_date + timedelta(minutes=1)

    def update_coin_data(self):
        self.logger.warning(f"**** {datetime.now()} ****")
        for coin in self.config.SUPPORTED_COIN_LIST:
            self.manager.set_ticker_price(coin + self.config.BRIDGE.symbol)

    def start_doobot_trading(self):
        self.logger.info("start_doobot_trading Starting!!!!!!!!!!!")

        # check if we can access API feature that require valid config
        try:
            _ = self.manager.get_account()   ## 바이낸스 현재 계좌정보 가지고오기
        except Exception as e:  # pylint: disable=broad-except
            self.logger.error("Couldn't access Binance API - API keys may be wrong or lack sufficient permissions")
            self.logger.error(e)
            return

        trader_list = list()

        # doobotx01 ~ 10 전략 셋팅
        for i in range(10):
            strategy_nm = "doobotx" + CommonUtil.integer_to_string_n(i + 1, 2)
            strategy = get_strategy(strategy_nm)
            if strategy is None:
                self.logger.error("Invalid strategy name")
                return
            logger = Logger(strategy_nm, self.db)
            logger.set_strategy_name(strategy_nm)
            trader = strategy(self.manager, self.db, logger, self.config)
            trader.initialize()
            trader_list.append(trader)

        schedule = SafeScheduler(self.logger)

        # 5분마다 돌게 셋팅
        for i in range(12):
            minute = 5 * i
            minut_str = CommonUtil.integer_to_string_n(minute, 2)
            for j in range(len(trader_list)):
                second = CommonUtil.integer_to_string_n(3 * j + 1, 2)
                schedule.every().hours.at(minut_str + ":" + second).do(trader_list[j].scout)

        # 5초 실시간 스카웃 셋팅
        schedule.every(5).seconds.do(trader_list[1 - 1].scout_realtime)  # doobotx01
        schedule.every(5).seconds.do(trader_list[2 - 1].scout_realtime)  # doobotx02
        schedule.every(5).seconds.do(trader_list[3 - 1].scout_realtime)  # doobotx03
        schedule.every(5).seconds.do(trader_list[4 - 1].scout_realtime)  # doobotx04
        schedule.every(5).seconds.do(trader_list[5 - 1].scout_realtime)  # doobotx05
        schedule.every(5).seconds.do(trader_list[6 - 1].scout_realtime)  # doobotx06
        schedule.every(5).seconds.do(trader_list[7 - 1].scout_realtime)  # doobotx07 실시간 조회 안함 (5분루핑만 적용)
        schedule.every(5).seconds.do(trader_list[8 - 1].scout_realtime)  # doobotx08
        schedule.every(5).seconds.do(trader_list[9 - 1].scout_realtime)  # doobotx09 실시간 조회 안함 (5분루핑만 적용)
        schedule.every(5).seconds.do(trader_list[10 - 1].scout_realtime)  # doobotx10

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        finally:
            self.manager.stream_manager.close()


