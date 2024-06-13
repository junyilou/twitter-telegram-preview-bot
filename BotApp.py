import logging
from twitterBot import handler_group
from telegram.ext import ApplicationBuilder
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

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
	bot.add_handlers(handler_group)
	bot.run_polling()

main()