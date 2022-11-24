from datetime import datetime

from binance_dootiger_bot.doobot_trading import DoobotTrading

if __name__ == "__main__":
    history = []
    dt = DoobotTrading()
    dt.start_doobot_trading()
