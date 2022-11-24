from datetime import datetime

from binance_dootiger_bot.doobot_trading import DoobotTrading

if __name__ == "__main__":
    history = []
    dt = DoobotTrading()
    dt.update_coin_data_history(datetime(2022, 8, 21, 0, 0), datetime(2022, 9, 1, 0, 0))

