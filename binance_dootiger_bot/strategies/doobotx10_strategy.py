import random
import sys
from datetime import datetime, timedelta

from binance_dootiger_bot.common.auto_trader import AutoTrader
from binance_dootiger_bot.common.common_util import CommonUtil
from binance_dootiger_bot.models import Coin
from binance_dootiger_bot.service.scoring_manager import ScoringManager

class Strategy(AutoTrader):     # AutoTrader 로 상속받아 생성된 전략파일
    def initialize(self):
        self.strategy_name = "doobotx10"
        self.initialize_current_coin()  # backtest 테이블 및 거래금액 초기 셋팅
        super().initialize()
        self.scoring = ScoringManager(self.config, self.db, self.logger, )

    def initialize_current_coin(self):
        """
        Decide what is the current coin, and set it up in the DB.
        backtest_history 테이블 셋팅
        """
        self.logger.debug("Strategy.initialize_current_coin Called")
        self.BUY_STD_USDT_BALANCE = 100
        self.BACKTEST_START_USDT_BALANCE = 10000

    def scout(self):
        """
        가격 변동을 감지해서 메시지 전송함
        """
        self.logger.debug("Strategy.scout Called")
        # self.logger.warning("전략수행(scout) alive check!!!!")
        # self.logger.warning(f"{self.manager.balances[self.strategy_name]}")

        for coin in self.config.SUPPORTED_COIN_LIST:
            ## 조회 전 코인 봉데이터 UPDATE
            self.manager.set_ticker_price(coin + self.config.BRIDGE.symbol, self.manager.datetime)

            self.account = self.db.get_backtest_history(self.strategy_name, coin)
            if self.account.total_coin_balance == 0:
                self.buy_coin(Coin(coin))

            if self.account.total_coin_balance != 0:
                self.cell_coin(Coin(coin))

    def scout_realtime(self):
        """
        가격 변동을 감지해서 메시지 전송함
        """
        for coin in self.config.SUPPORTED_COIN_LIST:
            self.account = self.db.get_backtest_history(self.strategy_name, coin)
            if self.account.total_coin_balance == 0:
                self.buy_coin_realtime(Coin(coin))

            if self.account.total_coin_balance != 0:
                self.cell_coin_realtime(Coin(coin))

    ## Realtime 매수처리
    def buy_coin_realtime(self, coin: Coin):
        self.logger.debug("Strategy.buy_coin_realtime Called")

        # 5분봉 30분봉 가격정보 가지고옴
        coin_price_5m_realtime = self.manager.get_historical_klines_realtime(coin.symbol + self.config.BRIDGE.symbol, "5m")
        coin_price_list_30 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "30m", datetime.now(), 30)

        if coin_price_5m_realtime is None:
            self.logger.info("경고!! 실시간 조회(get_historical_klines) 오류..")
            return False

        if coin_price_list_30 is None:
            self.logger.info("경고!! DB조회 오류!!! ")
            return False

        coin_price_list_30 = CommonUtil.query_to_dictionary(coin_price_list_30)
        cache_price = self.manager.cache.ticker_values.get(coin.symbol + self.config.BRIDGE.symbol, None)

        ################################ 점수 산정 ################################
        score = self.get_score_ohlcv_now(coin_price_5m_realtime, coin_price_list_30, cache_price)

        # 20점 이상이면 매수
        if score >= 20:
            self.logger.info("매수신호 감지되었습니다...")
            self.manager.buy_alt(self.strategy_name, coin, self.config.BRIDGE, float(self.BUY_STD_USDT_BALANCE), cache_price)  # 1000 USDT

    ## Realtime 익절처리
    def cell_coin_realtime(self, coin: Coin):
        self.logger.debug("Strategy.cell_coin_realtime Called")

        cache_price = self.manager.cache.ticker_values.get(coin.symbol + self.config.BRIDGE.symbol, None)
        per = CommonUtil.float_cut_decimal_n((cache_price - self.account.total_coin_price) / self.account.total_coin_price * 100, 2)
        self.logger.debug(f"[{self.strategy_name}] cache_price : {cache_price}, total_coin_price : {self.account.total_coin_price}, per: {per}")

        ###################### 부분익절 ######################
        if cache_price > self.account.total_coin_price * 1.005 \
                and self.manager.balances[self.strategy_name]['sell_more_cnt'] == 0:
            self.logger.info("리얼타임 부분익절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['sell_more_cnt'] = 1
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 50, cache_price)

        ###################### 익절 ######################
        if cache_price > self.account.total_coin_price * 1.008 \
                and self.manager.balances[self.strategy_name]['sell_more_cnt'] == 1:
            self.logger.info("리얼타임 익절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['sell_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100, cache_price)

        ###################### 손절 ######################
        if cache_price < self.account.total_coin_price * 0.995:
            self.logger.info("리얼타임 급하락 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['sell_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100, cache_price)

    def buy_coin(self, coin: Coin):
        self.logger.debug("Strategy.buy_coin Called")
        if self.manager.backtest_yn != True:
            return False

        if self.manager.backtest_yn == True:
            coin_price_list_5 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", self.manager.datetime - timedelta(minutes=5), 30)
            coin_price_list_30 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "30m", self.manager.datetime - timedelta(minutes=30), 30)
        else:
            coin_price_list_5 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", datetime.now(), 30)
            coin_price_list_30 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "30m", datetime.now(), 30)

        if coin_price_list_5 is None:
            self.logger.info("경고!! coin_price_list_5 DB조회 오류!!! ")
            return False

        if coin_price_list_30 is None:
            self.logger.info("경고!! coin_price_list_30 DB조회 오류!!! ")
            return False

        coin_price_list_5 = coin_price_list_5[0]
        coin_price_list_30 = CommonUtil.query_to_dictionary(coin_price_list_30)

        ################################ 점수 산정 ################################
        score = self.get_score_ohlcv_now(coin_price_list_5, coin_price_list_30, coin_price_list_5.close)

        # 20점 이상이면 매수
        if score >= 20:
            self.logger.info("매수신호 감지되었습니다...")
            self.manager.buy_alt(self.strategy_name, coin, self.config.BRIDGE, float(self.BUY_STD_USDT_BALANCE))  # 1000 USDT

    def cell_coin(self, coin: Coin):
        self.logger.debug("Strategy.cell_coin Called")

        account = self.db.get_backtest_history(self.strategy_name, coin)

        ##################### 시간초과 손절 ######################
        if self.manager.backtest_yn == True:
            son_datatime = self.manager.datetime
        else:
            son_datatime = datetime.now()
        if account.total_coin_balance != 0 \
                and self.manager.balances[self.strategy_name]['buy_more_cnt'] == 0 \
                and son_datatime >= self.account.datetime + timedelta(minutes=150):
            self.logger.info("물타기 전 시간초과 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['sell_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)

    def get_score_ohlcv_now(self, coin_price_5m_realtime: list, coin_price_list_30: list, cache_price=0):
        """
        5분봉으로 점수를 계산해서 return 해주는 함수
        """
        print("스코어링 스타트!!!!!!!!!!!!!!!")
        result_score = 0
        ########################################################################
        # 1. 실시간데이터와 가격 30분봉 비교
        ########################################################################
        score_1 = self.scoring.get_price_bigger_then_bf10_score(coin_price_list_30, cache_price)
        result_score += score_1

        ########################################################################
        # 2. 실시간 거래량(5분봉으로 환산) 이 직전봉(30분)의 5분평균의 5배 이상일 때
        ########################################################################
        score_2 = self.scoring.get_volume_over_value_than_bf1_score(coin_price_5m_realtime, coin_price_list_30)
        result_score += score_2

        # if score_2 >= 20:
        self.logger.debug(f"=== Report [{coin_price_list_30[0]['datetime']}]===\n"
                          f"** 실시간 가격 :::: {cache_price}\n"
                          f"1. 실시간 가격 30분봉 비교(상승) :::: {score_1}\n"
                          f"2. 실시간 거래량 대비 직전봉(30분)비교 :::: {score_2}\n"
                          )

        return result_score

