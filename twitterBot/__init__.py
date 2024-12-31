from telegram.ext import BaseHandler


def load() -> list[BaseHandler]:
	from .group import command_handler, group_handlers
	from .inline import inline_handler
	handler_group = [inline_handler, command_handler, *group_handlers]
	return handler_group