import re
from datetime import datetime
from typing import Any, Literal, Optional

# from modules.tweet import Tweet
from modules.util import bitsize, browser_agent, disMarkdown, time_delta
from modules.vxtwitter import Tweet
from telegram import InputMediaPhoto, Message, User
from telegram.constants import ParseMode
from telegram.error import BadRequest

url_regex = re.compile(r"\b(twitter|x)\.com/(.*?)/status/(\d+)", re.I)

class TweetModel:
	def __init__(self, tweet: Tweet) -> None:
		self.tweet: Tweet = tweet

	@property
	def user_str(self) -> str:
		user = self.tweet.user
		return f"*{disMarkdown(user.name, extra = "*")}* [\\@{disMarkdown(user.screen_name)}]({user.url})"

	@property
	def stat_str(self) -> str:
		return "  ".join(f"{k} {v:,}" for k, v in {
			"👁️": self.tweet.view_count,
			"🔄": self.tweet.retweet_count,
			"♥️": self.tweet.favourites_count}.items() if v is not None)

	@property
	def preview(self) -> str:
		diff = time_delta(dt1 = self.tweet.created, dt2 = datetime.now().astimezone(), items = 2)
		return f"*来自* {self.user_str}\n*发表于* {diff} 前".strip()

	async def download(self) -> dict[str, int]:
		from modules.util import request
		files: dict[str, int] = {}
		for i, e in enumerate(self.tweet.entities):
			filename = f"{self.tweet.entity_identifier}-{i + 1}.{e.format}"
			try:
				r = await request(e.url, mode = "raw", retry = 3, headers = browser_agent)
				with open(f"twitter/{filename}", "wb") as w:
					w.write(r)
				files[filename] = len(r)
			except:
				files[filename] = 0
		return files

	async def output_private(self) -> tuple[str, bool]:
		self.tweet = redirect(self.tweet)
		outputs = ["*Twitter 下载*", self.preview, disMarkdown(self.tweet.url, extra = "*")]
		if not self.tweet.entities:
			success, failed = "", "推文没有媒体信息"
		else:
			files = await self.download()
			success = "\n".join(f"{disMarkdown(filename)}: \\({disMarkdown(bitsize(size, width = 0, ks = 2 ** 10), wrap = "_")}\\)"
				for filename, size in files.items() if size)
			failed = "\n".join(disMarkdown(filename) for filename, size in files.items() if not size)
		outputs.extend((f"{cat}\n{txt}") for cat, txt in zip(("*成功下载*", "*失败下载* \\#失败"), (success, failed)) if txt)
		return "\n\n".join(outputs), any(failed)

	def output_group(self, from_user: Literal[True] | User = True,
		forward_user: Optional[str | User] = None) -> str:
		body, shared = disMarkdown("\n\n".join([self.tweet.text, self.stat_str, self.tweet.url]), extra = "`*"), ""
		match from_user, forward_user:
			case User(full_name = mu), str(du) | User(full_name = du):
				shared = f"{disMarkdown(mu, wrap = "*", extra = "*")} 转发自 {disMarkdown(du, wrap = "*", extra = "*")}:"
			case User(full_name = mu), _:
				shared = f"{disMarkdown(mu, wrap = "*", extra = "*")} 分享了:"
		video_strs, video_entities = [], [e for e in self.tweet.entities if e.telegram_type == "video"]
		if video_entities:
			if len(video_entities) == 1:
				video_strs = [f"🎬 [视频链接]({video_entities[0].url})", ""]
			else:
				video_strs = [" ".join([f"🎬 [视频{i + 1}]({v.url})" for i, v in enumerate(video_entities)]), ""]
		return "\n".join([shared, "", *video_strs, self.user_str, body])

def generate_kwargs(tweet: Tweet, text: str) -> dict[str, Any]:
	kwargs = {"parse_mode": ParseMode.MARKDOWN_V2, "quote": False}
	match len(tweet.entities):
		case 0:
			kwargs |= {"text": text, "disable_web_page_preview": True}
		case 1:
			e = tweet.entities[0]
			kwargs |= {"caption": text, e.telegram_type: e.url, "has_spoiler": tweet.sensitive}
		case _:
			kwargs |= {"caption": text, "media": [InputMediaPhoto(media = m.image_url)
				for m in tweet.entities if m.type == "photo"]}
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
			kwargs = {"parse_mode": ParseMode.MARKDOWN_V2, "quote": False, "text": kwargs["caption"], "disable_web_page_preview": True}
			sent = await message.reply_text(**kwargs)
	return sent