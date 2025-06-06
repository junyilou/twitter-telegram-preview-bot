from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes, InlineQueryHandler

from .models import url_regex

TELEGRAM_LOGO = "https://pbs.twimg.com/profile_images/1183117696730390529/LRDASku7.jpg"

def generate(items: list[tuple[str, str, str]], prefix: str, sep: str = "\n") -> str:
	return sep.join(f"https://{prefix}.com/{item[1]}/status/{item[2]}" for item in items)

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	try:
		query = update.inline_query
		assert query
		text = query.query
	except AssertionError:
		return
	items = url_regex.findall(text)
	if not items:
		await query.answer([])
		return

	if items[0][0] == "twitter":
		options = {"生成 vxtwitter.com 的预览链接": ("vxtwitter", TELEGRAM_LOGO)}
	else:
		options = {"生成 fixvx.com 的预览链接": ("fixvx", TELEGRAM_LOGO)}
	results = [InlineQueryResultArticle(id = str(uuid4()),
		title = title, description = (u := generate(items, prefix)),
		thumbnail_url = thumb,
		input_message_content = InputTextMessageContent(
			message_text = u,
			disable_web_page_preview = title.endswith("）")))
		for title, (prefix, thumb) in options.items()]
	await query.answer(results)

inline_handler = InlineQueryHandler(inline_query)