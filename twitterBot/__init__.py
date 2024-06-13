from telegram.ext import JobQueue

from .group import command_handler, group_handlers
from .inline import inline_handler

try:
	from .personal import personal_handler
	handler_group = [inline_handler, command_handler, personal_handler, *group_handlers]
except:
	handler_group = [inline_handler, command_handler, *group_handlers]

def add_jobs(job_queue: JobQueue) -> None:
	try:
		from .personal import twitter_stat, twitter_stat_time
		job_queue.run_daily(twitter_stat, twitter_stat_time)
	except:
		return

try:
	from modules.tweet import get_scrapper
	get_scrapper()
except FileNotFoundError:
	raise FileNotFoundError("Please deploy bot-scraper.cookies first") from None