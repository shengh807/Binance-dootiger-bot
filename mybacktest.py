from datetime import datetime, timedelta

from binance_dootiger_bot.backtest import Backtest

if __name__ == "__main__":
    history = []
    bt = Backtest()

    for manager in bt.backtest(datetime(2022, 3, 20), datetime(2022, 5, 1)):
        print("------")
        print("TIME:", manager.datetime)
        print("------")

    print(f"*********************** 백테스트 종료 DB 확인하세요 ***********************")
