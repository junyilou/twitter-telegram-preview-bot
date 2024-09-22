from .group import command_handler, group_handlers
from .inline import inline_handler

handler_group = [inline_handler, command_handler, *group_handlers]

try:
	from modules.tweet import get_scrapper
	get_scrapper()
except FileNotFoundError:
	raise FileNotFoundError("Please deploy bot-scraper.cookies first") from None