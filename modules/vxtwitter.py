import asyncio
import json
import re
from datetime import datetime
from html import unescape
from typing import Any, Optional

from modules.util import request

ACCEPT = ["jpg", "png", "gif", "mp4", "mov", "ts"]
DTFORMAT = "%a %b %d %H:%M:%S %z %Y"

class User:
	def __init__(self, dct: dict[str, Any]) -> None:
		self.name: str = dct["user_name"]
		self.screen_name: str = dct["user_screen_name"]
		self.url: str = f"https://x.com/{self.screen_name}"
		self.avatar = re.sub(r"http[s]://pbs\.twimg\.com/profile_images/(\d+)/([^_/]+)(_[a-z]+)?\.(\w+)",
				r"https://pbs.twimg.com/profile_images/\1/\2.\4", dct["user_profile_image_url"])

	def __repr__(self) -> str:
		return f"<User: {self.name} (@{self.screen_name})>"

class Entity:
	def __init__(self, dct: dict[str, Any], idx: int) -> None:
		self.idx: int = idx + 1
		VXTABLE = {"image": "photo", "gif": "animated_gif"}
		self.type: str = VXTABLE.get(dct["type"], dct["type"])
		if self.type == "photo":
			search = re.search(r"http[s]://pbs\.twimg\.com/media/([^\.]+)\.([a-z]+)", dct["url"])
			if not search:
				raise ValueError(f"URL does not match: {dct["url"]}")
			k, f = search.groups()
			self.url = f"https://pbs.twimg.com/media/{k}?format={f}&name=orig"
			self.alter_url: str = self.url.replace("name=orig", "name=large")
			self.image_url: str = self.url
			self.format: str = f
			self.telegram_type = "photo"
		elif self.type in ["video", "animated_gif"]:
			self.url: str = dct["url"]
			self.alter_url: str = self.url
			self.image_url: str = dct["thumbnail_url"]
			self.format: str = "mp4"
			self.telegram_type = "video"
		else:
			raise ValueError(f"Unsupported Type: {self.type}")

	def __repr__(self) -> str:
		translate = {"photo": "Photo", "video": "Video", "animated_gif": "GIF"}
		return f"<{translate[self.type]} Entity {self.idx}>"

class Tweet:
	def __init__(self, dct: dict[str, Any], shout: bool = False) -> None:
		if "tweet" in dct:
			dct = dct["tweet"]
		self.raw: dict[str, Any] = dct
		self.id: str = dct["tweetID"]
		self.user: User = User(dct)
		self.created: datetime = datetime.strptime(dct["date"], DTFORMAT)
		self.url: str = f"https://x.com/{self.user.screen_name}/status/{self.id}"

		self.text_short: str = unescape(dct["text"])
		self.text: str = self.text_short
		self.language: Optional[str] = dct["lang"]
		self.sensitive: bool = dct["possibly_sensitive"]

		try:
			self.entities: list[Entity] = [Entity(d, idx) for idx, d in enumerate(dct["media_extended"])]
		except:
			if shout:
				raise
			self.entities = []
		self.entity_identifier: str = f"{self.user.screen_name}-{self.id}"

		self.quote_id: Optional[str] = None
		self.quote: Optional[Tweet] = None
		self.retweet_id: Optional[str] = None
		self.retweet: Optional[Tweet] = None
		if (quote := dct.get("qrt")):
			self.quote = Tweet(quote)
			self.quote_id = self.quote.id

		self.reply_user_screen_name: Optional[str] = None
		self.reply: Optional[Tweet] = None
		self.reply_url: Optional[str] = None
		if dct["conversationID"] != dct["tweetID"]:
			self.reply_id = dct["conversationID"]
			if (screen_name := re.search(r"^@?(\w){1,15}", self.text)):
				self.reply_user_screen_name = screen_name.group().removeprefix("@")
				self.reply_url = f"https://x.com/{self.reply_user_screen_name}/status/{self.reply_id}"

		self.favourites_count: int = dct["likes"]
		self.reply_count: int = dct["replies"]
		self.retweet_count: int = dct["retweets"]
		self.view_count: Optional[int] = None

	def elements(self, accept: Optional[list[str]] = None) -> list[str]:
		accept = accept or ACCEPT
		result, pattern = [], "|".join(accept)
		_ = [result.append(i[0]) for i in re.findall(r"[\'\"](http[^\"\']*\.(" + pattern +
			"))+[\'\"]?", json.dumps(self.raw, ensure_ascii = False)) if i[0] not in result]
		return sorted(result)

	def repr(self, display: bool = True) -> str:
		main = self.id
		user = f"by {self.user}" if display else ""
		media = f"{len(self.entities)} Media" if self.entities and display else ""
		quote = f"quote from: {self.quote.repr(display = False)}" if self.quote and display else ""
		retweet = f"retweet from: {self.retweet.repr(display = False)}" if self.retweet and display else ""
		reply = f"reply to: {self.reply.repr(display = False)}" if self.reply and display else ""
		text = ", ".join(i for i in [main, user, media, quote, retweet, reply] if i)
		return f"<Tweet {text}>"

	def __repr__(self) -> str:
		return self.repr(display = True)

def get_id(tweet_id: int | str) -> str:
	return re.findall(r"[0-9]{16,}", str(tweet_id))[0]

async def get_tweet(tweet_id: str, retry: int = 3, shout: bool = False) -> Optional[Tweet]:
	try:
		i = int(tweet_id)
	except ValueError:
		i = int(get_id(tweet_id))
	url = f"https://api.vxtwitter.com/Twitter/status/{i}"
	for _ in range(retry):
		output = await request(url, mode = "json")
		if output:
			break
		await asyncio.sleep(1)
	return Tweet(output, shout = shout)