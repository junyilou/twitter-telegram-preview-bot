import asyncio
import json
import re
from datetime import datetime
from html import unescape
from typing import Any, Optional

from twitter.scraper import Scraper

ACCEPT = ["jpg", "png", "gif", "mp4", "mov", "ts"]
DTFORMAT = "%a %b %d %H:%M:%S %z %Y"

class User:
	def __init__(self, dct: dict[str, Any]) -> None:
		self.id: str = dct["rest_id"]
		legacy: dict[str, Any] = dct["legacy"]
		self.name: str = legacy["name"]
		self.screen_name: str = legacy["screen_name"]
		self.created: datetime = datetime.strptime(legacy["created_at"], DTFORMAT)
		self.url: str = f"https://x.com/{self.screen_name}"

		self.favourites_count: int = legacy["favourites_count"]
		self.followers_count: int = legacy["followers_count"]
		self.following_count: int = legacy["friends_count"]
		self.media_count: int = legacy["media_count"]
		self.statuses_count: int = legacy["statuses_count"]

		self.avatar: str = "https://abs.twimg.com/sticky/default_profile_images/default_profile.png"
		self.banner: Optional[str] = None
		if not legacy["default_profile_image"]:
			self.avatar = re.sub(r"http[s]://pbs\.twimg\.com/profile_images/(\d+)/([^_/]+)(_[a-z]+)?\.(\w+)",
				r"https://pbs.twimg.com/profile_images/\1/\2.\4", legacy["profile_image_url_https"])
		if "profile_banner_url" in legacy:
			self.banner = re.sub(r"http[s]://pbs\.twimg\.com/profile_banners/(\d+)/(\d+)(/\w*)?",
				r"https://pbs.twimg.com/profile_banners/\1/\2/1500x500", legacy["profile_banner_url"])

		self.description: Optional[str] = legacy.get("description") or None
		self.link: Optional[str] = legacy.get("url") or None
		self.location: Optional[str] = legacy.get("location") or None

	def __repr__(self) -> str:
		return f"<User: {self.name} (@{self.screen_name})>"

class Entity:
	def __init__(self, dct: dict[str, Any]) -> None:
		self.id: str = dct["id_str"]
		self.type: str = dct["type"]
		if self.type == "photo":
			search = re.search(r"http[s]://pbs\.twimg\.com/media/([^\.]+)\.([a-z]+)", dct['media_url_https'])
			if not search:
				raise ValueError(f"URL does not match: {dct['media_url_https']}")
			k, f = search.groups()
			self.url = f"https://pbs.twimg.com/media/{k}?format={f}&name=orig"
			self.alter_url: str = self.url.replace("name=orig", "name=large")
			self.image_url: str = self.url
			self.format: str = f
			self.telegram_type = "photo"
		elif self.type in ["video", "animated_gif"]:
			urls = sorted([i for i in dct["video_info"]["variants"]
				if "bitrate" in i and i["content_type"] == "video/mp4"],
				key = lambda k: k["bitrate"], reverse = True)
			self.url: str = urls[0]["url"]
			self.alter_url: str = urls[int(len(urls) / 2)]["url"]
			self.image_url: str = dct["media_url_https"]
			self.format: str = "mp4"
			self.telegram_type = "video"
		else:
			raise ValueError(f"Unsupported Type: {self.type}")

	def __repr__(self) -> str:
		translate = {"photo": "Photo", "video": "Video", "animated_gif": "GIF"}
		return f"<{translate[self.type]} Entity {self.id}>"

class Tweet:
	def __init__(self, dct: dict[str, Any], shout: bool = False) -> None:
		if "tweet" in dct:
			dct = dct["tweet"]
		self.raw: dict[str, Any] = dct
		legacy: dict[str, Any] = dct["legacy"]
		self.id: str = legacy["id_str"]
		self.user_id: str = legacy["user_id_str"]
		assert dct["core"]["user_results"]["result"]["rest_id"] == self.user_id
		self.user: User = User(dct["core"]["user_results"]["result"])
		self.created: datetime = datetime.strptime(legacy["created_at"], DTFORMAT)
		self.url: str = f"https://x.com/{self.user.screen_name}/status/{self.id}"

		self.text_short: str = unescape(legacy["full_text"])
		try:
			note_tweet = dct["note_tweet"]["note_tweet_results"]
			result = unescape(note_tweet["result"]["text"])
			assert result
			self.text: str = result
		except:
			self.text: str = self.text_short
		self.language: Optional[str] = legacy.get("lang")
		self.sensitive: bool = legacy.get("possibly_sensitive", False)

		try:
			self.entities: list[Entity] = [Entity(d) for d in legacy.get("extended_entities", {}).get("media", [])]
		except:
			if shout:
				raise
			self.entities = []
		self.entity_identifier: str = f"{self.user.screen_name}-{self.id}"

		self.quote_id: Optional[str] = None
		self.quote: Optional[Tweet] = None
		self.retweet_id: Optional[str] = None
		self.retweet: Optional[Tweet] = None
		if "quoted_status_id_str" in legacy:
			if "quoted_status_result" in dct:
				self.quote_id = legacy["quoted_status_id_str"]
				self.quote = Tweet(dct["quoted_status_result"]["result"], shout = shout)
			elif "retweeted_status_result" in legacy:
				self.retweet_id = legacy["quoted_status_id_str"]
				self.retweet = Tweet(legacy["retweeted_status_result"]["result"], shout = shout)

		self.reply_id: Optional[str] = None
		self.reply_user_id: Optional[str] = None
		self.reply_user_name: Optional[str] = None
		self.reply_user_screen_name: Optional[str] = None
		self.reply: Optional[Tweet] = None
		self.reply_url: Optional[str] = None
		if "in_reply_to_status_id_str" in legacy:
			self.reply_id = legacy["in_reply_to_status_id_str"]
			self.reply_user_id = legacy["in_reply_to_user_id_str"]
			self.reply_user_name = next((i["name"] for i in legacy["entities"].get("user_mentions", []) if i["id_str"] == self.reply_user_id), None)
			self.reply_user_screen_name = legacy["in_reply_to_screen_name"]
			self.reply_url = f"https://x.com/{self.reply_user_screen_name}/status/{self.reply_id}"

		self.favourites_count: int = legacy["favorite_count"]
		self.quote_count: int = legacy["quote_count"]
		self.reply_count: int = legacy["reply_count"]
		self.retweet_count: int = legacy["retweet_count"]
		self.view_count: Optional[int] = None
		try:
			assert "views" in dct and "count" in dct["views"]
			self.view_count = int(dct["views"]["count"])
		except:
			pass

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

def login(email: str, username: str, password: str) -> None:
	# refer to trevorhobenshield/twitter-api-client
	scraper = Scraper(email, username, password)
	scraper.save_cookies("bot-scraper")

def get_scrapper() -> Scraper:
	return Scraper(cookies = "bot-scraper.cookies", save = False, pbar = False)

async def get_thread(tweet_id: str, scraper: Optional[Scraper] = None, shout: bool = False) -> Optional[Tweet]:
	scraper = scraper or get_scrapper()
	try:
		assert tweet_id.isdigit()
	except AssertionError:
		tweet_id = get_id(tweet_id)
	loop = asyncio.get_running_loop()
	output = await loop.run_in_executor(None, scraper.tweets_details, [int(tweet_id)])
	data = next(i for i in next(iter(output[0]["data"].values()))["instructions"] if i["type"] == "TimelineAddEntries")
	tweets: list[Tweet] = []
	for entry in data["entries"]:
		try:
			item, key = entry, ("content", "itemContent", "tweet_results", "result")
			for k in key:
				item = item.get(k)
				assert item
			tweets.append(Tweet(item, shout = shout))
		except AssertionError:
			continue
	dct = {t.id: t for t in tweets}
	for o in dct.values():
		if o.reply_id and o.reply_id in dct:
			o.reply = dct[o.reply_id]
			o.reply_url = o.reply.url
	return dct.get(tweet_id)

async def get_tweet(tweet_id: str, scraper: Optional[Scraper] = None, shout: bool = False) -> Optional[Tweet]:
	scraper = scraper or get_scrapper()
	try:
		i = int(tweet_id)
	except ValueError:
		i = int(get_id(tweet_id))
	l: list[int | str] = [i]
	loop = asyncio.get_running_loop()
	output = await loop.run_in_executor(None, scraper.tweets_by_id, l)
	try:
		return Tweet(output[0]["data"]["tweetResult"]["result"], shout = shout)
	except:
		if shout:
			raise
		return