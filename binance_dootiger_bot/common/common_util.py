import math
from sqlalchemy import inspect
from sqlalchemy.orm import Query

# from pandas import DataFrame
# import talib as ta

class CommonUtil:
    def object_as_dict(obj):
        return {c.key: getattr(obj, c.key)
                for c in inspect(obj).mapper.column_attrs}

    @staticmethod
    def query_to_dictionary(query_list: Query):
        result_dict = []
        for query in query_list:
            # print(CommonUtil.object_as_dict(result))
            result_dict.append(CommonUtil.object_as_dict(query))

        return result_dict
    
    ## Integer 를 String 으로 변환
    @staticmethod
    def integer_to_string_n(i: int, n: int = 0):
        output = str(i)

        if n != 0:
            for i in range(n - len(output)):
                output = "0" + output

        return output

    ## float 소숫점 자릿수 올림처리
    @staticmethod
    def float_cut_decimal_n(i: float, n: int = 2):
        output = math.floor(i * 10 ** n) / float(10 ** n)

        return output

    @staticmethod
    def add_ohlcv_ma(query_list: list, minute: int = 5):
        list_cnt = len(query_list) - minute  # Looping 횟수 = 전체갯수 - 기준이평선(5)

        # 거래량 증감률 봉 단위로 셋팅
        for i in range(list_cnt):
            close_sum = 0
            for j in range(minute):
                close_sum += query_list[i+j]["close"]

            query_list[i]["MA" + str(minute)] = close_sum / minute

        return query_list


    ################################## PANDAS, TALIB 사용 불가 시 ##################################
    @staticmethod
    def add_ohlcv_bband(query_list: list):
        n = 20
        k = 2
        # 20 이평선 구하기
        list_cnt = len(query_list) - n  # Looping 횟수 = 전체갯수 - 기준이평선(20)

        # 거래량 증감률 봉 단위로 셋팅
        for i in range(list_cnt):
            close_sum = 0
            for j in range(n):
                close_sum += query_list[i+j]["close"]

            query_list[i]["MA" + str(n)] = close_sum / n

        # 20개 표준편차 구하기
        for i in range(list_cnt):
            vsum = 0
            for j in range(n):
                vsum += (query_list[i+j]["close"] - query_list[i]["MA" + str(n)]) ** 2
            variance = vsum / n     # 분산 구하기
            stdev = math.sqrt(variance)    # 표준편차 구하기

            ################ 볼린저밴드 값 추가필요 #####################
            query_list[i]["BBAND_MIDDLE"] = query_list[i]["MA" + str(n)]
            query_list[i]["BBAND_UPPER"] = query_list[i]["MA" + str(n)] + k * stdev
            query_list[i]["BBAND_LOWER"] = query_list[i]["MA" + str(n)] - k * stdev

        return query_list

    @staticmethod
    def add_ohlcv_rsi(query_list: list):
        n = 14
        data_list = []
        for query in query_list:
            data_dict = {}
            data_dict['datetime'] = query['datetime']
            data_dict['close'] = query['close']
            data_list.append(data_dict)

        # U, D 셋팅
        for i in range(len(data_list)-1):
            data_list[i]["U"] = 0
            data_list[i]["D"] = 0
            data_list[i]["AU"] = 0
            data_list[i]["AD"] = 0
            theta = data_list[i]["close"] - data_list[i + 1]["close"]
            if theta >= 0:
                data_list[i]["U"] += theta
            else:
                data_list[i]["D"] -= theta

        # AU, AD 셋팅
        for i in range(len(data_list) - n):
            u_sum = 0
            d_sum = 0
            for j in range(n):
                u_sum += data_list[i+j]["U"]
                d_sum += data_list[i+j]["D"]
            data_list[i]["AU"] = u_sum / n
            data_list[i]["AD"] = d_sum / n

        # 수정 AU, AD 셋팅
        for i in range(len(data_list) - n - 1):
            ad_i = len(data_list) - n - 2 - i
            data_list[ad_i]["AU"] = (data_list[ad_i + 1]["AU"] * (n - 1) + data_list[ad_i]["U"]) / n
            data_list[ad_i]["AD"] = (data_list[ad_i + 1]["AD"] * (n - 1) + data_list[ad_i]["D"]) / n

        # RSI 셋팅
        for i in range(len(data_list) - n - 1):
            rs = data_list[i]["AU"] / data_list[i]["AD"]
            query_list[i]["RSI"] = round(rs / (1 + rs) * 100, 4)

        return query_list

    ##############################################################################################

    # @staticmethod
    # def listdict_to_dataframe(input_list: list):
    #     result_df = DataFrame(input_list)
    #     # result_df.set_index('datetime', drop=False, inplace=True)
    #
    #     return result_df
    #
    # @staticmethod
    # def dataframe_to_listdict(input_df: DataFrame):
    #     result_list = input_df.to_dict('records')
    #
    #     return result_list
    #
    # @staticmethod
    # def add_ohlcv_bband(query_list: list):
    #     # DataFrame 사용하기위해 생성
    #     query_list_df = CommonUtil.listdict_to_dataframe(query_list)
    #
    #     df = query_list_df.sort_values(by='datetime', axis=0, ascending=True)  # 날짜순으로 오름차순 정렬
    #     df['BBAND_UPPER'], df['BBAND_MIDDLE'], df['BBAND_LOWER'] = ta.BBANDS(df['close'], 20, 2)  # 볼벤 셋팅
    #     df.dropna(subset=['BBAND_UPPER'], inplace=True)  # NaN이 있는 컬럼은 날려버림
    #     df.sort_values(by='datetime', axis=0, ascending=False, inplace=True)  # 날짜순으로 내림차순 정렬
    #
    #     return_list = CommonUtil.dataframe_to_listdict(df)
    #     return return_list
    #
    # @staticmethod
    # def add_ohlcv_rsi(query_list: list):
    #     # DataFrame 사용하기위해 생성
    #     query_list_df = CommonUtil.listdict_to_dataframe(query_list)
    #
    #     df = query_list_df.sort_values(by='datetime', axis=0, ascending=True)  # 날짜순으로 오름차순 정렬
    #     df['RSI'] = ta.RSI(df['close'], 14)  # RSI 셋팅
    #     df.dropna(subset=['RSI'], inplace=True)  # NaN이 있는 컬럼은 날려버림
    #     df.sort_values(by='datetime', axis=0, ascending=False, inplace=True)  # 날짜순으로 내림차순 정렬
    #
    #     return_list = CommonUtil.dataframe_to_listdict(df)
    #     return return_list



