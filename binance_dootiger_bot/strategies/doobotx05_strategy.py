import random
import sys
from datetime import datetime, timedelta

from binance_dootiger_bot.common.auto_trader import AutoTrader
from binance_dootiger_bot.common.common_util import CommonUtil
from binance_dootiger_bot.models import Coin
from binance_dootiger_bot.service.scoring_manager import ScoringManager


class Strategy(AutoTrader):     # AutoTrader 로 상속받아 생성된 전략파일
    def initialize(self):
        self.strategy_name = "doobotx05"
        self.initialize_current_coin()  # backtest 테이블 및 거래금액 초기 셋팅
        super().initialize()
        self.scoring = ScoringManager(self.config, self.db, self.logger, )

    def initialize_current_coin(self):
        """
        Decide what is the current coin, and set it up in the DB.
        backtest_history 테이블 셋팅
        """
        self.logger.debug("Strategy.initialize_current_coin Called")
        self.BUY_STD_USDT_BALANCE = 50
        self.BACKTEST_START_USDT_BALANCE = 10000

    def scout(self):
        """
        가격 변동을 감지해서 메시지 전송함
        """
        self.logger.debug("Strategy.scout Called")
        # self.logger.warning("전략수행(scout) alive check!!!!")
        # self.logger.warning(f"{self.manager.balances[self.strategy_name]}")

        for coin in self.config.SUPPORTED_COIN_LIST:

            # self.buy_coin(Coin(coin))  # TEST!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            ## 조회 전 코인 봉데이터 UPDATE
            self.manager.set_ticker_price(coin + self.config.BRIDGE.symbol, self.manager.datetime)

            self.account = self.db.get_backtest_history(self.strategy_name, coin)
            if self.account.total_coin_balance == 0:
                self.buy_coin(Coin(coin))

            if self.account.total_coin_balance > 0:
                self.cell_coin(Coin(coin))
                # self.buy_more_coin(Coin(coin))

    def scout_realtime(self):
        """
        가격 변동을 감지해서 메시지 전송함
        """
        # self.logger.warning("전략수행(scout_realtime) check!!!!")
        for coin in self.config.SUPPORTED_COIN_LIST:
            self.account = self.db.get_backtest_history(self.strategy_name, coin)
            if self.account.total_coin_balance > 0:
                self.cell_coin_realtime(Coin(coin))

    ## Realtime 익절처리
    def cell_coin_realtime(self, coin: Coin):
        self.logger.debug("Strategy.cell_coin_realtime Called")

        cache_price = self.manager.cache.ticker_values.get(coin.symbol + self.config.BRIDGE.symbol, None)
        per = CommonUtil.float_cut_decimal_n((cache_price - self.account.total_coin_price) / self.account.total_coin_price * 100, 2)
        self.logger.debug(f"[{self.strategy_name}] cache_price : {cache_price}, total_coin_price : {self.account.total_coin_price}, per: {per}")

        if cache_price > self.account.total_coin_price * 1.01:
            self.logger.info("리얼타임 익절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100, cache_price)

        if cache_price < self.account.total_coin_price * 0.995:
            self.logger.info("리얼타임 급하락 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100, cache_price)

    def buy_coin(self, coin: Coin):
        # 매수 전략
        self.logger.debug("Strategy.buy_coin Called")

        # 최종 매도 후 1시간 동안 매수 금지
        if self.manager.backtest_yn == True:
            son_datatime = self.manager.datetime
        else:
            son_datatime = datetime.now()
        if son_datatime < self.account.datetime + timedelta(minutes=120) \
                and (self.account.trade_coin_price != 0
                     or self.account.trade_coin_balance != 0
                     or self.account.total_coin_price != 0
                     or self.account.total_coin_balance != 0):
            return True

        if self.manager.backtest_yn == True:
            coin_price_list_5 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", self.manager.datetime - timedelta(minutes=5), 30)
            coin_price_list_30 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "30m", self.manager.datetime - timedelta(minutes=30), 30)
        else:
            coin_price_list_5 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", datetime.now(), 30)
            coin_price_list_30 = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "30m", datetime.now(), 30)

        if coin_price_list_5 is None:
            self.logger.info("경고!! DB조회 오류!!! ")
            return False

        if coin_price_list_30 is None:
            self.logger.info("경고!! DB조회 오류!!! ")
            return False

        coin_price_list_5 = CommonUtil.query_to_dictionary(coin_price_list_5)
        coin_price_list_30 = CommonUtil.query_to_dictionary(coin_price_list_30)

        ################################ 점수 산정 ################################
        score = self.get_score_ohlcv_now(coin_price_list_5, coin_price_list_30)

        # 90점 이상이면 매수
        if score >= 10:
            print("10% 매수!!")
            self.logger.info("매수신호 감지되었습니다...")
            self.manager.buy_alt(self.strategy_name, coin, self.config.BRIDGE, float(self.BUY_STD_USDT_BALANCE))  # 1000 USDT


    def buy_more_coin(self, coin: Coin):
        # 뭍타기 전략
        self.logger.debug("Strategy.buy_more_coin Called")

        if self.manager.backtest_yn == True:
            coin_price_list = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", self.manager.datetime - timedelta(minutes=5), 7)
        else:
            coin_price_list = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", datetime.now(), 10)

        if coin_price_list is None:
            self.logger.info("경고!! DB조회 오류!!! ")
            return False

        # 직전봉의 등락폭이 -1% 이상이고, 아랫꼬리가 윗꼬리보다 길 때
        change = (coin_price_list[0].close - self.manager.balances[self.strategy_name][coin.symbol+"_price"]) / coin_price_list[0].open
        up_tail = coin_price_list[0].high - coin_price_list[0].open
        down_tail = coin_price_list[0].close - coin_price_list[0].low

        self.logger.warning(f"=============== Report ===============\n"
                            f"물타기 횟수 : {self.manager.balances[self.strategy_name]['buy_more_cnt']}\n"
                            f"등락율 : {float(round(change * 100, 3))}\n"
                            f"윗꼬리길이 : {float(round(up_tail, 3))}\n"
                            f"아랫꼬리길이 : {float(round(down_tail, 3))}")

        buy_more_cnt = self.manager.balances[self.strategy_name]['buy_more_cnt']
        usdt_total = self.manager.balances[self.strategy_name][self.config.BRIDGE.symbol+"_total"]
        buy_more_amount = float(self.BUY_STD_USDT_BALANCE) * (1 ** (buy_more_cnt + 1))

        if change < -0.01:
            # 1% 이상 떨어지면 물타기 금지
            return True

        if change < -0.005 * (buy_more_cnt + 1) \
                and down_tail > up_tail * 5 \
                and usdt_total > buy_more_amount:
            self.logger.info("물타기 매수신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] += 1
            self.manager.buy_alt(self.strategy_name, coin, self.config.BRIDGE, buy_more_amount)


    def cell_coin(self, coin: Coin):
        # 매도 전략
        self.logger.debug("Strategy.cell_coin Called")
        account = self.db.get_backtest_history(self.strategy_name, coin)

        if self.manager.backtest_yn == True:
            coin_price_list = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", self.manager.datetime - timedelta(minutes=5), 5)
        else:
            coin_price_list = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", datetime.now(), 10)

        if coin_price_list is None:
            self.logger.info("경고!! DB조회 오류!!! ")
            return False

        ###################### 익절 ######################
        if coin_price_list[0].close > account.total_coin_price * 1.01:
            # 현재 가지고있는 코인의 per 만큼 매도한다
            self.logger.info("익절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)

        ###################### 손절 ######################
        if coin_price_list[0].close < account.total_coin_price * 0.99 \
            and self.manager.balances[self.strategy_name]['buy_more_cnt'] >= 1:
            # 현재 가지고있는 코인의 per 만큼 매도한다
            self.logger.info("손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)


        ###################### 물타기 전 손절 ######################
        # 1. 급하락 손절
        if coin_price_list[0].close < account.total_coin_price * 0.995 \
                and self.manager.balances[self.strategy_name]['buy_more_cnt'] == 0:
            self.logger.info("물타기 전 급하락 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)

        # 2. 시간초과 손절
        if self.manager.backtest_yn == True:
            son_datatime = self.manager.datetime
        else:
            son_datatime = datetime.now()
        if account.total_coin_balance > 0 \
                and self.manager.balances[self.strategy_name]['buy_more_cnt'] == 0 \
                and son_datatime >= self.account.datetime + timedelta(minutes=120):
            self.logger.info("물타기 전 시간초과 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)


        ##################### 추매물량 일부정리 ######################
        if coin_price_list[0].close > account.total_coin_price and self.manager.balances[self.strategy_name]['buy_more_cnt'] > 0:
            self.logger.info("추매물량 일부정리 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] -= 1
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 50)

        change = (coin_price_list[0].close - self.manager.balances[self.strategy_name][coin.symbol+"_price"]) / coin_price_list[0].open
        self.logger.warning(f"=============== Report ===============\n"
                            f"물타기 횟수 : {self.manager.balances[self.strategy_name]['buy_more_cnt']}\n"
                            f"등락율 : {float(round(change * 100, 3))}\n")

    def get_score_ohlcv_now(self, coin_price_list_5: list, coin_price_list_30: list):
        """
        5분봉으로 점수를 계산해서 return 해주는 함수
        """
        print("스코어링 스타트!!!!!!!!!!!!!!!")
        result_score = 0

        ########################################################################
        # 1. 30분봉 RSI 점수
        ########################################################################
        score_5 = self.scoring.get_price_to_rsi_score4(coin_price_list_30)
        result_score += score_5

        self.logger.warning(f"===== Report [{coin_price_list_5[0]['datetime']}] =====\n"
                            f"1. RSI 점수 :::: {score_5}\n"
                            )

        return result_score

