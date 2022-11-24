from datetime import datetime
import logging.handlers

from binance_dootiger_bot.common.telegram_message import Telegram
from binance_dootiger_bot.service.database_manager import Database
from binance_dootiger_bot.common.config import Config


class Logger:

    Logger = None
    TelegramHandler = None

    def __init__(self, logging_service="crypto_trading", db: Database = None,):
        # Logger setup
        self.Logger = logging.getLogger(f"{logging_service}_logger")
        self.Logger.setLevel(logging.DEBUG)
        self.Logger.propagate = False
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.config = Config()
        self.strategy_name = "doobot"

        # DB Setup
        if db is not None:
            self.db = db

        # default is "logs/crypto_trading.log"
        fh = logging.FileHandler(f"logs/{logging_service}.log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        self.Logger.addHandler(fh)

        # logging to console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.Logger.addHandler(ch)

        # telegram handler
        self.TelegramHandler = Telegram()

    def log(self, message, level="info"):
        print(message)

        if level == "info":
            self.Logger.info(message)
        elif level == "warning":
            self.Logger.warning(message)
        elif level == "error":
            self.Logger.error(message)
        elif level == "debug":
            self.Logger.debug(message)

        if level == "info":
            try:
                ## TO-DO : 중복발송 방지로직 추가
                # 동일날짜에 동일내용 있으면 PASS
                is_send = self.db.get_message_history(datetime.now(), str(message))

                if is_send is None or is_send is not None:
                    self.TelegramHandler.send_message(str(message))
                    self.db.set_message_history(str(message))  # DB Insert

            except Exception as e:  # pylint: disable=broad-except
                self.Logger.error(e)

        if level == "warning":
            try:
                self.TelegramHandler.send_message_alivecheck(str(message))
                self.db.set_message_history(str(message))  # DB Insert
            except Exception as e:  # pylint: disable=broad-except
                self.Logger.error(e)

    def info(self, message):
        self.log(f"[{self.strategy_name}] {datetime.now()}\n{message}", "info")

    def warning(self, message):
        self.log(f"[{self.strategy_name}] {datetime.now()}\n{message}", "warning")

    def error(self, message):
        self.log(message, "error")

    def debug(self, message):
        self.log(message, "debug")

    def set_strategy_name(self, strategy_name: str):
        self.strategy_name = strategy_name