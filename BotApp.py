import logging
from warnings import filterwarnings

from telegram.ext import ApplicationBuilder
from telegram.warnings import PTBUserWarning

from twitterBot import load

token = "TOKEN" # Create your bot using @BotFather

def set_logger() -> None:
	logging.getLogger("httpx").propagate = False
	logging.getLogger("apscheduler.executors").propagate = False
	logging.getLogger("apscheduler.scheduler").setLevel(logging.ERROR)
	logging.basicConfig(filename = "BotApp.log",
		format = "[%(asctime)s %(name)s %(levelname)s] %(message)s",
		level = logging.INFO, filemode = "a", datefmt = "%F %T")

def main() -> None:
	filterwarnings(action = "ignore", message = r".*CallbackQueryHandler", category = PTBUserWarning)
	bot = ApplicationBuilder().token(token).build()
	bot.add_handlers(load())
	bot.run_polling()

main()