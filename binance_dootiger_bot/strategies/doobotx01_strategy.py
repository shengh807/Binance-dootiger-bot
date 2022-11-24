import random
import sys
from datetime import datetime, timedelta

from binance_dootiger_bot.common.auto_trader import AutoTrader
from binance_dootiger_bot.models import Coin
from binance_dootiger_bot.common.common_util import CommonUtil


class Strategy(AutoTrader):     # AutoTrader 로 상속받아 생성된 전략파일
    def initialize(self):
        self.strategy_name = "doobotx01"
        self.initialize_current_coin()  # backtest 테이블 및 거래금액 초기 셋팅
        self.logger.debug("Strategy.initialize Called")
        super().initialize()

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
            ## 조회 전 코인 봉데이터 UPDATE
            self.manager.set_ticker_price(coin + self.config.BRIDGE.symbol)

            self.account = self.db.get_backtest_history(self.strategy_name, coin)
            if self.account.total_coin_balance == 0:
                self.buy_coin(Coin(coin))

            if self.account.total_coin_balance > 0:
                self.cell_coin(Coin(coin))
                self.buy_more_coin(Coin(coin))

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

        if cache_price > self.account.total_coin_price * 1.005:
            self.logger.info("리얼타임 익절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100, cache_price)

        if cache_price < self.account.total_coin_price * 0.99:
            self.logger.info("리얼타임 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100, cache_price)

    def buy_coin(self, coin: Coin):
        # 매수 전략
        self.logger.debug("Strategy.buy_coin Called")

        # 최종 매도 후 60분 동안 매수 금지
        son_datatime = datetime.now()
        if self.manager.backtest_yn == True:        # 백테스트 용 코드
            son_datatime = self.manager.datetime
            
        if son_datatime < self.account.datetime + timedelta(minutes=60) \
                and (self.account.trade_coin_price != 0
                     or self.account.trade_coin_balance != 0
                     or self.account.total_coin_price != 0
                     or self.account.total_coin_balance != 0):
            self.logger.debug(f"[{self.strategy_name}] 최종 매도 후 60분 동안 매수 금지")
            return True

        if self.manager.backtest_yn == True:
            coin_price_list = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", self.manager.datetime - timedelta(minutes=5), 10)
        else:
            coin_price_list = self.db.get_coin_price_list(coin.symbol + self.config.BRIDGE.symbol, "5m", datetime.now(), 10)

        if coin_price_list is None:
            self.logger.info("경고!! DB조회 오류!!! ")
            return False

        price_down_cnt = 0
        price_over_down_cnt = 0
        list_high = 0
        list_low = 9999999

        for coin_price in coin_price_list:
            # 6개봉 이상 하락이고, 0.3 프로 하락이 2개 이상일 때
            if coin_price.close - coin_price.open < 0:
                price_down_cnt += 1
            if (coin_price.close - coin_price.open) / coin_price.open < -0.001:
                price_over_down_cnt += 1

            # 7개 봉 고가, 저가 차이가 -1% 이상일 때,
            if list_high < coin_price.high:
                list_high = coin_price.high
            if list_low > coin_price.low:
                list_low = coin_price.low

        change = (list_low - list_high) / list_high

        up_tail = coin_price_list[0].high - coin_price_list[0].open
        down_tail = coin_price_list[0].close - coin_price_list[0].low

        self.logger.warning(f"=============== Report ===============\n"
                            f"하락 봉 개수 : {price_down_cnt}\n"
                            f"급하락 봉 개수 : {price_over_down_cnt}\n"
                            f"고가 : {list_high}, 저가 : {list_low}\n"
                            f"등락율 : {float(round(change * 100, 3))}\n"
                            f"윗꼬리길이 : {float(round(up_tail, 3))}\n"
                            f"아랫꼬리길이 : {float(round(down_tail, 3))}")

        # 직전봉의 등락폭이 0.1 % 이내이고, 아랫꼬리가 윗꼬리보다 길 때
        if price_down_cnt >= 6 and price_over_down_cnt >= 2 and change < -0.005 and down_tail > up_tail:
            print("10% 매수!!")
            self.logger.info("매수신호 감지되었습니다...")
            self.manager.buy_alt(self.strategy_name, coin, self.config.BRIDGE, float(self.BUY_STD_USDT_BALANCE))  # 1000 USDT

    def buy_more_coin(self, coin: Coin):
        # 뭍타기 전략
        self.logger.debug("Strategy.buy_more_coin Called")

        ############################ 매수전략 3 ##################################
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
                            f"물타기 횟수 : {self.manager.balances[self.strategy_name]['buy_more_cnt'] }\n"
                            f"등락율 : {float(round(change * 100, 3))}\n"
                            f"윗꼬리길이 : {float(round(up_tail, 3))}\n"
                            f"아랫꼬리길이 : {float(round(down_tail, 3))}")


        if change < -0.02 * (self.manager.balances[self.strategy_name]['buy_more_cnt'] + 1) and down_tail > up_tail \
                and self.manager.balances[self.strategy_name][self.config.BRIDGE.symbol+"_total"] > float(self.BUY_STD_USDT_BALANCE) * (2 ** (self.manager.balances[self.strategy_name]['buy_more_cnt'] + 1)):
            print("10% 매수!!")
            self.logger.info("물타기 매수신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] += 1
            self.manager.buy_alt(self.strategy_name, coin, self.config.BRIDGE, float(self.BUY_STD_USDT_BALANCE) * (2 ** (self.manager.balances[self.strategy_name]['buy_more_cnt'] + 1)))  # 500 USDT

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
        if coin_price_list[0].close > account.total_coin_price * 1.005:
            # 현재 가지고있는 코인의 per 만큼 매도한다
            self.logger.info("익절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)

        ###################### 손절 ######################
        if coin_price_list[0].close < account.total_coin_price * 0.96 and self.manager.balances[self.strategy_name]['buy_more_cnt'] == 1:

            # 물타고 3개봉 지켜보기 룰 추가
            if self.manager.backtest_yn == True:
                son_datatime = self.manager.datetime
            else:
                son_datatime = datetime.now()

            if self.manager.balances[self.strategy_name]['buy_more_cnt'] < 2 or son_datatime > self.account.datetime + timedelta(minutes=15):
                # 현재 가지고있는 코인의 per 만큼 매도한다
                self.logger.info("손절 매도신호 감지되었습니다...")
                self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
                self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)

        ##################### 추매물량 일부정리 ######################
        if coin_price_list[0].close > account.total_coin_price and self.manager.balances[self.strategy_name]['buy_more_cnt'] > 0:
            self.logger.info("추매물량 일부정리 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] -= 1
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 50)

        ###################### 물타기 전 손절 ######################
        # 1. 급하락 손절
        if coin_price_list[0].close < account.total_coin_price * 0.97 \
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
                and son_datatime >= self.account.datetime + timedelta(minutes=120):
            self.logger.info("물타기 전 시간초과 손절 매도신호 감지되었습니다...")
            self.manager.balances[self.strategy_name]['buy_more_cnt'] = 0
            self.manager.sell_alt(self.strategy_name, coin, self.config.BRIDGE, 100)

