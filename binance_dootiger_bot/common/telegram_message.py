import telegram

TELEGRAM_TOKEN = "2127354179:AAFtZ1Cep-8HETCBrBRKtR_GLWsVSM5JKZ4"

class Telegram:
    def __init__(self):
        print("Telegram.__init__ Called")
        self.bot = telegram.Bot(token=TELEGRAM_TOKEN)

    def send_message(self, text):
        print("Telegram.send_message Called")
        print("send_to_telegram : {}".format(text))
        return self.bot.send_message(chat_id='@dootigerchannel', disable_web_page_preview='true', text=text)

    def send_message_alivecheck(self, text):
        print("Telegram.send_message_alivecheck Called")
        print("send_to_telegram : {}".format(text))
        return self.bot.send_message(chat_id='@dootigerchannelalive', text=text)

if __name__ == "__main__":
    telegram = Telegram()
    return_code = telegram.send_message("안녕하세요 테스트입니다")



