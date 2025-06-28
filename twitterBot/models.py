import re
from datetime import datetime
from typing import Any, Literal, Optional

from modules.util import disMarkdown, time_delta
from modules.vxtwitter import Tweet
from modules.vxtwitter import User as TwitterUser
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      InputMediaPhoto, Message)
from telegram import User as TelegramUser
from telegram.constants import ParseMode
from telegram.error import BadRequest

url_regex = re.compile(r"\b(twitter|x)\.com/(.*?)/status/(\d+)", re.I)

def user_str(user: TwitterUser) -> str:
	return f"*{disMarkdown(user.name, extra = "*")}* [\\@{disMarkdown(user.screen_name)}]({user.url})"

def stat_str(tweet: Tweet) -> str:
	return "  ".join(f"{k} {v:,}" for k, v in {"👁️": tweet.view_count, "🔄": tweet.retweet_count,
		"♥️": tweet.favourites_count}.items() if v is not None)

def preview(tweet: Tweet) -> str:
	extra = ""
	diff = time_delta(dt1 = tweet.created, dt2 = datetime.now().astimezone(), items = 2)
	if tweet.quote_id:
		extra += f"\n*引用推文* [{tweet.quote_id}]({tweet.quote_url})"
	if tweet.reply_id:
		extra += f"\n*回复推文* [{tweet.reply_id}]({tweet.reply_url})"
	return f"*来自* {user_str(tweet.user)}\n*发表于* {diff} 前{extra}".strip()

def output(tweet: Tweet, from_user: Literal[True] | TelegramUser = True,
	forward_user: Optional[str | TelegramUser] = None) -> str:
	body, shared = disMarkdown("\n\n".join([tweet.text, stat_str(tweet), tweet.url]), extra = "*"), ""
	match from_user, forward_user:
		case TelegramUser(full_name = mu), str(du) | TelegramUser(full_name = du):
			shared = f"{disMarkdown(mu, wrap = "*", extra = "*")} 转发自 {disMarkdown(du, wrap = "*", extra = "*")}:"
		case TelegramUser(full_name = mu), _:
			shared = f"{disMarkdown(mu, wrap = "*", extra = "*")} 分享了:"
	video_strs, video_entities = [], [e for e in tweet.entities if e.telegram_type == "video"]
	if video_entities:
		if len(video_entities) == 1:
			video_strs = [f"🎬 [视频链接]({video_entities[0].url})", ""]
		else:
			video_strs = [" ".join([f"🎬 [视频{i + 1}]({v.url})" for i, v in enumerate(video_entities)]), ""]
	extra = []
	if tweet.quote_id:
		prefix, url = "", tweet.quote_url
		if tweet.quote:
			other = "另" if tweet.quote.user == tweet.user else ""
			prefix = f" {disMarkdown(tweet.quote.user.name, extra = "*")} 的{other}"
			url = tweet.quote.url
		extra.append(f"引用了{prefix}一条[推文]({url})")
	if tweet.reply_id:
		prefix, url = "", tweet.reply_url
		if tweet.reply:
			other = "另" if tweet.reply.user == tweet.user else ""
			prefix = f" {disMarkdown(tweet.reply.user.name, extra = "*")} 的{other}"
			url = tweet.reply.url
		extra.append(f"回复了{prefix}一条[推文]({url})")
	if extra:
		extra.append("")
	return "\n".join([shared, "", *video_strs, user_str(tweet.user), *extra, body])

def generate_kwargs(tweet: Tweet, text: str) -> dict[str, Any]:
	def generate_keyboard() -> dict[str, InlineKeyboardMarkup]:
		try:
			assert tweet.reply_id or tweet.quote_id
			assert len(tweet.entities) <= 1
		except AssertionError:
			return {}
		buttons = [[]]
		if rid := tweet.reply_id:
			buttons[0].append(InlineKeyboardButton("补充回复内容", callback_data = f"TWEET _YES {rid}"))
		if qid := tweet.quote_id:
			buttons[0].append(InlineKeyboardButton("补充引用内容", callback_data = f"TWEET _YES {qid}"))
		if buttons[0]:
			button = InlineKeyboardButton("忽略补充内容", callback_data = f"TWEET IGNORE _")
			if len(buttons[0]) > 1:
				buttons.append([button])
			else:
				buttons[0].append(button)
			return {"reply_markup": InlineKeyboardMarkup(buttons)}
		return {}

	kwargs = {"parse_mode": ParseMode.MARKDOWN_V2, "do_quote": False}
	match len(tweet.entities):
		case 0:
			kwargs |= {"text": text, "disable_web_page_preview": True}
		case 1:
			e = tweet.entities[0]
			kwargs |= {"caption": text, e.telegram_type: e.url, "has_spoiler": tweet.sensitive}
		case _:
			kwargs |= {"caption": text, "media": [InputMediaPhoto(media = m.image_url,
				has_spoiler = tweet.sensitive) for m in tweet.entities if m.type == "photo"]}
	kwargs.update(generate_keyboard())
	return kwargs

def redirect(t: Tweet) -> Tweet:
	while not t.entities:
		try:
			t = next(i for i in (t.retweet, t.reply, t.quote) if i)
		except StopIteration:
			break
	return t

async def match_send(message: Message, kwargs: dict[str, Any]) -> Optional[Message]:
	sent = None
	try:
		match kwargs:
			case {"text": _}:
				sent = await message.reply_text(**kwargs)
			case {"photo": _}:
				sent = await message.reply_photo(**kwargs)
			case {"media": _}:
				sents = await message.reply_media_group(**kwargs)
				sent = sents[0]
			case {"video": _}:
				sent = await message.reply_video(**kwargs)
	except BadRequest:
		if "caption" in kwargs:
			kwargs = {"parse_mode": ParseMode.MARKDOWN_V2, "do_quote": False,
				"text": kwargs["caption"], "disable_web_page_preview": True}
			sent = await message.reply_text(**kwargs)
	return sent