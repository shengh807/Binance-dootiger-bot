import random
import sys
from datetime import datetime

from binance_dootiger_bot.common.auto_trader import AutoTrader


class Strategy(AutoTrader):     # AutoTrader 로 상속받아 생성된 전략파일
    def initialize(self):
        self.logger.debug("Strategy.initialize Called")
        super().initialize()
        # self.initialize_current_coin()  # current_coin_history 테이블 셋팅

    def scout(self):
        """
        가격 변동을 감지해서 메시지 전송함
        """
        self.logger.debug("Strategy.scout Called")
        self.logger.warning("[doobot] 전략수행(scout) alive check!!!!")
        
        # 코인리스트로 for문
        for coin in self.config.SUPPORTED_COIN_LIST:
            # 최근 5개 데이터 가지고오기
            inc_signal_cnt = 0
            dec_signal_cnt = 0
            inc_change = 0
            dec_change = 0
            coin_price_list = self.db.get_coin_price_list(coin + self.config.BRIDGE.symbol, "5m", self.manager.datetime)

            ############ 전략1. 가격 급/등락 주 체크해서 메시지 보내기 ############
            for coin_price in coin_price_list:
                change = (coin_price.close - coin_price.open) / coin_price.open * 100
                if change > 0.5:
                    inc_signal_cnt = inc_signal_cnt + 1
                    if inc_change < change:
                        inc_change = change
                if change < -0.5:
                    dec_signal_cnt = dec_signal_cnt + 1
                    if dec_change > change:
                        dec_change = change

            if inc_signal_cnt >= 2:
                self.logger.info("---가격(close) 상승---\n"
                                 f"{coin_price_list[0].datetime} {coin_price_list[0].interval} 확인요망\n"
                                 "[" + coin + "USDT] " + str(inc_change) + "% \n"
                                 f"https://www.binance.com/en/futures/{coin}USDT")
            if dec_signal_cnt >= 2:
                self.logger.info("---가격(close) 하락---\n"
                                 f"{coin_price_list[0].datetime} {coin_price_list[0].interval} 확인요망\n"
                                 "[" + coin + "USDT] " + str(dec_change) + "% \n"
                                 f"https://www.binance.com/en/futures/{coin}USDT")

            ############ 전략2. 거래량 급등 주 체크해서 메시지 보내기 ############
            if coin_price_list[0].volume > coin_price_list[1].volume * 4:
                volume_change = coin_price_list[0].volume / coin_price_list[1].volume
                self.logger.info("★★★★거래량(Volume) 급등★★★★\n"
                                 f"{coin_price_list[0].datetime} {coin_price_list[0].interval} 확인요망\n"
                                 "[" + coin + "USDT] " + str(volume_change) + " 배 급등\n"
                                 f"https://www.binance.com/en/futures/{coin}USDT")

            elif coin_price_list[0].volume > coin_price_list[2].volume * 4:
                volume_change = coin_price_list[0].volume / coin_price_list[2].volume
                self.logger.info("★★★★거래량(Volume) 급등★★★★\n"
                                 f"{coin_price_list[0].datetime} {coin_price_list[0].interval} 확인요망\n"
                                 "[" + coin + "USDT] " + str(volume_change) + " 배 급등\n"
                                 f"https://www.binance.com/en/futures/{coin}USDT")

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
