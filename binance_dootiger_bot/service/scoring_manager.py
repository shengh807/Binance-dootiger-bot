from datetime import datetime

from binance_dootiger_bot.common.common_util import CommonUtil
from binance_dootiger_bot.common.config import Config
from binance_dootiger_bot.service.database_manager import Database
from binance_dootiger_bot.common.logger import Logger


class ScoringManager:
    def __init__(self, config: Config, db: Database, logger: Logger):
        # initializing the client class calls `ping` API endpoint, verifying the connection
        self.logger = logger
        self.logger.debug("ScoringManager.__init__ Called")
        self.db = db
        self.config = config

    def get_price_down_cnt_score(self, coin_price_list: str, stick_cnt: int = 10):
        """
        최근 하락봉 갯수 Counting 해서 점수로 계산
        카운팅 봉 갯수 : 10
        """
        price_down_cnt = 0

        for i in range(stick_cnt):
            if coin_price_list[i]["close"] - coin_price_list[i]["open"] < 0:
                price_down_cnt += 1

        # price_down_cnt 로 점수내기 (1:매수(최초), 1:하락봉 갯수)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "1", price_down_cnt)

        return return_score

    def get_price_over_down_cnt_score(self, coin_price_list: list, stick_cnt: int = 10, price_down_per: float = -0.001):
        """
        최근 과매도 하락봉 갯수 Counting 해서 점수로 계산
        """
        price_over_down_cnt = 0

        for i in range(stick_cnt):
            if (coin_price_list[i]["close"] - coin_price_list[i]["open"]) / coin_price_list[i]["open"] < price_down_per:
                price_over_down_cnt += 1

        # price_down_cnt 로 점수내기 (1:매수(최초), 2:과매도 하락봉 갯수)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "2", price_over_down_cnt)

        return return_score

    def get_volume_change_before_score(self, coin_price_list: list):
        """
        최근 거래량 급등 점수로 계산
        """
        stick_cnt = 10

        # 거래량 증감률 봉 단위로 셋팅
        for i in range(stick_cnt):
            coin_price_list[i]["volume_change"] = coin_price_list[i]["volume"] / coin_price_list[i+1]["volume"]

        # 직전 봉 거래량 증감률 셋팅
        volume_change = coin_price_list[0]["volume_change"]

        # price_down_cnt 로 점수내기 (1:매수(최초), 3:거래량 급등)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "3", volume_change)

        return return_score

    def get_volume_change_before_range_score(self, coin_price_list: list, stick_cnt: int = 10):
        """
        최근 거래량 10개봉 합과 그 전 10개봉 합 비율 점수로 계산
        """
        volumn_sum_1_10 = 0
        volumn_sum_11_20 = 0

        # 거래량 증감률 봉 단위로 셋팅
        for i in range(stick_cnt):
            volumn_sum_1_10 += coin_price_list[i]["volume"]
            volumn_sum_11_20 += coin_price_list[i+10]["volume"]

        # 직전 봉 거래량 증감률 셋팅
        volume_change = volumn_sum_1_10 / volumn_sum_11_20

        # price_down_cnt 로 점수내기 (1:매수(최초), 3:거래량 급등)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "3", volume_change)

        return return_score

    def get_price_to_ma_ratio_score(self, coin_price_list: list, ma_num: int):
        """
        현재가격 이평선 이격도 분석 점수
        """
        # ohlcv List에 이평선(7) 추가
        coin_price_list = CommonUtil.add_ohlcv_ma(coin_price_list, ma_num)

        # 직전 봉 이평선과의 이격률
        close_ma_position = (coin_price_list[0]["close"] - coin_price_list[0]["MA"+str(ma_num)]) / coin_price_list[0]["MA"+str(ma_num)]

        # 종가와 이평선 이격으로 점수내기 (1:매수(최초), 4:이평선과의 이격)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "4", close_ma_position)

        return return_score

    def get_price_to_bollinger_ratio_score(self, coin_price_list: list):
        """
        현재가격 볼린저밴드 이격도 분석 점수
        """
        # 리스트에 볼린저밴드 추가
        coin_price_list = CommonUtil.add_ohlcv_bband(coin_price_list)

        # 종가가 볼린저밴드 안에서의 위치 (단위 : %)
        bband_position = (coin_price_list[0]["close"] - coin_price_list[0]["BBAND_LOWER"]) \
                         / (coin_price_list[0]["BBAND_UPPER"] - coin_price_list[0]["BBAND_LOWER"]) * 100

        # 종가와 볼린저밴드 위치로 점수내기 (1:매수(최초), 5:볼린저밴드 내에서의 위치)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "5", bband_position)

        return return_score

    def get_price_to_rsi_score(self, coin_price_list: list):
        """
        RSI 분석 점수
        """
        # df에 RSI 추가
        coin_price_list = CommonUtil.add_ohlcv_rsi(coin_price_list)

        # 종가가 볼린저밴드 안에서의 위치 (단위 : %)
        rsi_value = coin_price_list[0]["RSI"]

        # 종가와 볼린저밴드 위치로 점수내기 (1:매수(최초), 6:RSI 점수)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "6", rsi_value)

        return return_score

    def get_price_to_rsi_score2(self, coin_price_list: list):
        """
        RSI 분석 점수
        """
        # df에 RSI 추가
        coin_price_list = CommonUtil.add_ohlcv_rsi(coin_price_list)

        # 종가가 볼린저밴드 안에서의 위치 (단위 : %)
        rsi_value = coin_price_list[0]["RSI"]

        # 종가와 볼린저밴드 위치로 점수내기 (1:매수(최초), 6:RSI 점수)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "6", rsi_value)

        # 2022.01.25 직전봉 RSI를 빼줌
        rsi_value_bf1 = coin_price_list[1]["RSI"]
        return_score -= self.db.get_score_value(self.logger.strategy_name, "1", "6", rsi_value_bf1)

        return return_score

    def get_stick_tail_vs_header_score(self, coin_price_list: list):
        """
        윗꼬리 대비 아랫꼬리 비율 분석 점수
        """
        up_tail = 0
        down_tail = 0
        mid = 0

        if coin_price_list[0]["open"] - coin_price_list[0]["close"] > 0:  # 하락봉일때
            up_tail = coin_price_list[0]["high"] - coin_price_list[0]["open"]
            down_tail = coin_price_list[0]["close"] - coin_price_list[0]["low"]
        else:  # 상승일때
            up_tail = coin_price_list[0]["high"] - coin_price_list[0]["close"]
            down_tail = coin_price_list[0]["open"] - coin_price_list[0]["low"]

        # 아랫꼬리 비율로 점수내기 (1:매수(최초), 7:아랫꼬리 모양)
        tail_header_length_rate = (down_tail + 1) / (up_tail + 1)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "7", tail_header_length_rate)

        return return_score


    def get_stick_tail_vs_body_length_score(self, coin_price_list: list):
        """
        몸통길이 대비 아랫꼬리 비율 분석 점수
        """
        up_tail = 0
        down_tail = 0
        mid = 0

        if coin_price_list[0]["open"] - coin_price_list[0]["close"] > 0:  # 하락봉일때
            down_tail = coin_price_list[0]["close"] - coin_price_list[0]["low"]
            mid = coin_price_list[0]["open"] - coin_price_list[0]["close"]
        else:  # 상승일때
            down_tail = coin_price_list[0]["open"] - coin_price_list[0]["low"]
            mid = coin_price_list[0]["close"] - coin_price_list[0]["open"]

        # 아랫꼬리 비율로 점수내기 (1:매수(최초), 8:몸통 대비 아랫꼬리 길이)
        tail_body_length_rate = (down_tail + 1) / (mid + 1)
        return_score = self.db.get_score_value(self.logger.strategy_name, "1", "8", tail_body_length_rate)

        return return_score

    def get_volume_single_change_before_score(self, coin_price_list: list):
        """
        2전봉 > 1전봉
        1전봉 > 0전봉
        """
        return_score = 0

        if coin_price_list[2]["volume"] - coin_price_list[1]["volume"] > 0 \
                and coin_price_list[1]["volume"] - coin_price_list[0]["volume"] > 0:
            return_score = 10

        return return_score

    def get_price_over_down_cnt_score2(self, coin_price_list: list, stick_cnt: int = 10, price_down_per: float = -0.001):

        return_score = 0
        price_over_down_cnt = 0

        for i in range(5):
            if (coin_price_list[i]["close"] - coin_price_list[i]["open"]) / coin_price_list[i]["open"] < price_down_per:
                price_over_down_cnt += 1

        if price_over_down_cnt >= 2:
            return_score = 10

        return return_score

    def get_length_uptail_downtail_compare_score(self, coin_price_list: list):
        """
        1전봉 아랫꼬리 > 윗꼬리 * 3
        0전봉 아랫꼬리 > 윗꼬리 * 3
        """
        return_score = 0

        for i in range(10):
            # 하락봉일때
            if coin_price_list[i]["open"] - coin_price_list[i]["close"] > 0:
                coin_price_list[i]["up_tail"] = coin_price_list[i]["high"] - coin_price_list[i]["open"]
                coin_price_list[i]["down_tail"] = coin_price_list[i]["close"] - coin_price_list[i]["low"]
            # 상승봉일때
            else:
                coin_price_list[i]["up_tail"] = coin_price_list[i]["high"] - coin_price_list[i]["close"]
                coin_price_list[i]["down_tail"] = coin_price_list[i]["open"] - coin_price_list[i]["low"]

        if (coin_price_list[1]["down_tail"] + 1) / (coin_price_list[1]["up_tail"] + 1) > 3 \
                and (coin_price_list[0]["down_tail"] + 1) / (coin_price_list[0]["up_tail"] + 1) > 3:
            return_score = 10

        return return_score

    def get_price_to_bollinger_ratio_score2(self, coin_price_list: list):
        """
        2,1전봉 BB 30% 이하
        0전봉 BB 30% 이상
        """
        return_score = 0

        # 리스트에 볼린저밴드 추가
        coin_price_list = CommonUtil.add_ohlcv_bband(coin_price_list)

        # 종가가 볼린저밴드 안에서의 위치 (단위 : %)
        bband_position_0 = (coin_price_list[0]["close"] - coin_price_list[0]["BBAND_LOWER"]) \
                         / (coin_price_list[0]["BBAND_UPPER"] - coin_price_list[0]["BBAND_LOWER"]) * 100
        bband_position_1 = (coin_price_list[1]["close"] - coin_price_list[1]["BBAND_LOWER"]) \
                         / (coin_price_list[1]["BBAND_UPPER"] - coin_price_list[1]["BBAND_LOWER"]) * 100
        bband_position_2 = (coin_price_list[2]["close"] - coin_price_list[2]["BBAND_LOWER"]) \
                         / (coin_price_list[2]["BBAND_UPPER"] - coin_price_list[2]["BBAND_LOWER"]) * 100

        if bband_position_0 > 30 \
                and bband_position_1 < 30 \
                and bband_position_2 < 30:
            return_score = 10

        return return_score

    def get_price_to_rsi_score3(self, coin_price_list: list):
        """
        2,1,0전봉 RSI점수 30 이하
        """
        return_score = 0

        # df에 RSI 추가
        coin_price_list = CommonUtil.add_ohlcv_rsi(coin_price_list)

        if 40 > coin_price_list[0]["RSI"] > coin_price_list[1]["RSI"] + 1:
            return_score = 50

        return return_score

    def get_price_to_rsi_score4(self, coin_price_list: list):
        """
        2,1,0전봉 RSI점수 30 이하
        """
        return_score = 0

        # df에 RSI 추가
        coin_price_list = CommonUtil.add_ohlcv_rsi(coin_price_list)

        if 50 > coin_price_list[0]["RSI"] \
                and coin_price_list[0]["RSI"] < coin_price_list[1]["RSI"] - 2 \
                and coin_price_list[1]["RSI"] < coin_price_list[2]["RSI"] - 2 \
                and coin_price_list[2]["RSI"] < coin_price_list[3]["RSI"] - 2:
            return_score = 10

        return return_score

    def get_price_to_ma_compare_score(self, coin_price_list: list):
        """
        현재가격 이평선 이격도 분석 점수
        """
        return_score = 0

        # ohlcv List에 이평선(7) 추가
        coin_price_list = CommonUtil.add_ohlcv_ma(coin_price_list, 5)
        coin_price_list = CommonUtil.add_ohlcv_ma(coin_price_list, 20)

        if coin_price_list[1]["MA5"] - coin_price_list[0]["MA5"] < 0 \
                and coin_price_list[1]["MA20"] - coin_price_list[0]["MA20"] > 0:
            return_score = 10

        return return_score

    def get_price_shape_bf0_bf1_score(self, coin_price_list: str):
        """
        0전봉 하락, 1전봉 상승이면 점수
        """
        return_score = 0

        if coin_price_list[0]["open"] - coin_price_list[0]["close"] < 0 \
                and coin_price_list[1]["open"] - coin_price_list[1]["close"] > 0:
            return_score = 10

        return return_score

    def get_price_compare_bf0_bf1_score(self, coin_price_list: str):
        """
        0봉전 시가 < 볼벤 하단
        0봉전 종가 > 1봉전 시가 대비 종가의 20%
        0봉전 종가 < 1봉전 시가 대비 종가의 50%
        1봉전 종가 < 볼벤 하단
        1봉전 시가 > 볼벤 하단
        """
        return_score = 0

        # 리스트에 볼린저밴드 추가
        coin_price_list = CommonUtil.add_ohlcv_bband(coin_price_list)

        # 하락봉일때
        if coin_price_list[1]["open"] - coin_price_list[1]["close"] > 0:
            coin_price_list[1]["10PER"] = coin_price_list[1]["close"] + (coin_price_list[1]["open"] - coin_price_list[1]["close"]) * 10 / 100
            coin_price_list[1]["80PER"] = coin_price_list[1]["close"] + (coin_price_list[1]["open"] - coin_price_list[1]["close"]) * 80 / 100
        # 상승봉일때
        else:
            coin_price_list[1]["10PER"] = coin_price_list[1]["open"] + (coin_price_list[1]["close"] - coin_price_list[1]["open"]) * 10 / 100
            coin_price_list[1]["80PER"] = coin_price_list[1]["open"] + (coin_price_list[1]["close"] - coin_price_list[1]["open"]) * 80 / 100

        if coin_price_list[0]["open"] < coin_price_list[0]["BBAND_MIDDLE"] \
                and coin_price_list[0]["close"] > coin_price_list[1]["10PER"] \
                and coin_price_list[0]["close"] < coin_price_list[1]["80PER"] \
                and coin_price_list[1]["low"] < coin_price_list[1]["BBAND_MIDDLE"] \
                and coin_price_list[1]["open"] > coin_price_list[1]["BBAND_LOWER"]:
            return_score = 10

        return return_score

    def get_tail_length_downtail_compare_score(self, coin_price_list: list):
        """
        1전봉 아랫꼬리 > 윗꼬리 * 3
        """
        return_score = 0

        for i in range(10):
            # 하락봉일때
            if coin_price_list[i]["open"] - coin_price_list[i]["close"] > 0:
                coin_price_list[i]["up_tail"] = coin_price_list[i]["high"] - coin_price_list[i]["open"]
                coin_price_list[i]["down_tail"] = coin_price_list[i]["close"] - coin_price_list[i]["low"]
                coin_price_list[i]["body_len"] = coin_price_list[i]["open"] - coin_price_list[i]["close"]
            # 상승봉일때
            else:
                coin_price_list[i]["up_tail"] = coin_price_list[i]["high"] - coin_price_list[i]["close"]
                coin_price_list[i]["down_tail"] = coin_price_list[i]["open"] - coin_price_list[i]["low"]
                coin_price_list[i]["body_len"] = coin_price_list[i]["close"] - coin_price_list[i]["open"]

        if coin_price_list[1]["down_tail"] > coin_price_list[1]["body_len"] * 1:
            return_score = 10

        return return_score

    def get_price_bigger_then_bf10_score(self, coin_price_list: str, cache_price):
        """
        실시간 가격(cache_price)이 10개봉 고가보다 크면 점수
        """
        return_score = 0
        high_price = 0

        for i in range(10):
            if coin_price_list[i]["high"] > high_price:
                high_price = coin_price_list[i]["high"]

        if cache_price > high_price:
            return_score = 10

        print(f"high_price : {high_price}, cache_price : {cache_price}..")

        return return_score

    def get_price_smaller_then_bf10_score(self, coin_price_list: str, cache_price):
        """
        실시간 가격(cache_price)이 10개봉 고가보다 크면 점수
        """
        return_score = 0
        low_price = coin_price_list[0]["low"]

        for i in range(10):
            if coin_price_list[i]["low"] < low_price:
                low_price = coin_price_list[i]["low"]

        if cache_price < low_price:
            return_score = 10

        print(f"low_price : {low_price}, cache_price : {cache_price}..")

        return return_score

    def get_volume_over_value_than_bf1_score(self, coin_price_5m_realtime: list, coin_price_list_30: list):
        """
        실시간 거래량(5분봉으로 환산) 이 직전봉(30분)의 5분평균의 5배 이상일 때
        """
        return_score = 0
        td = coin_price_5m_realtime.datetime
        minute = td.minute % 5
        second = td.second
        to_second = minute * 60 + second

        if to_second == 0:
            to_second = 300

        volumn_5m_change_realtime = float(coin_price_5m_realtime.volume) / to_second * 300
        volumn_5m_change_from_30m = (coin_price_list_30[0]["volume"] + coin_price_list_30[1]["volume"] + coin_price_list_30[2]["volume"]) / 18

        print(f"실시간 거래량 5분봉[예상] : {volumn_5m_change_realtime}, 직전30분봉 거래량 5분봉 환산 : {volumn_5m_change_from_30m}..")
        if volumn_5m_change_realtime > volumn_5m_change_from_30m * 3.5:
            return_score = 10

        return return_score