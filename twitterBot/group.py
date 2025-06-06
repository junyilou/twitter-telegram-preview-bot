import logging
from typing import cast

from modules.util import disMarkdown
from modules.vxtwitter import Tweet, get_tweet
from telegram import (ChatMemberAdministrator, InlineKeyboardButton,
                      InlineKeyboardMarkup, Message, MessageOriginHiddenUser,
                      MessageOriginUser, Update, User)
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from .models import generate_kwargs, match_send, output, preview, url_regex


async def entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	try:
		message = update.message
		assert message and message.text and message.from_user
		assert context.chat_data is not None
	except AssertionError:
		return

	is_private = message.chat_id == message.from_user.id
	for _, _, tid in url_regex.findall(message.text):
		try:
			assert (tweet := await get_tweet(tweet_id = tid, shout = True, recursive = 1))
		except Exception as exp:
			logging.error(f"[处理推文失败] {tid}: {exp!r}")
			await message.reply_markdown_v2(disMarkdown(f"*未能处理你的请求*\nTweet ID: {tid}"))
			continue
		if is_private:
			await entry_manual(message, tweet)
		else:
			await entry_group(message, tweet, context)

async def entry_group(message: Message, tweet: Tweet, context: ContextTypes.DEFAULT_TYPE) -> None:
	assert context.chat_data is not None and message.text is not None
	text = f"*要生成推文预览吗？*\n\n{preview(tweet)}"
	keyboard = [[InlineKeyboardButton("生成", callback_data = f"TWEET YES {tweet.id}"),
		InlineKeyboardButton("忽略", callback_data = f"TWEET NO {tweet.id}")]]
	if message.forward_origin or " " not in message.text.strip():
		keyboard[0].insert(0, InlineKeyboardButton("生成并删除", callback_data = f"TWEET ALL {tweet.id}"))
	await message.reply_markdown_v2(text, disable_web_page_preview = True,
		reply_markup = InlineKeyboardMarkup(keyboard), do_quote = False)
	context.chat_data[tweet.id] = tweet, message

async def entry_manual(message: Message, tweet: Tweet) -> None:
	assert message.from_user is not None
	await callback_main(message, message, message.from_user, tweet, "YES")

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	try:
		query = update.callback_query
		message = update.effective_message
		assert query and message
		await query.answer()
		assert query.data
		_, mode, tid = query.data.split(" ")
		assert context.chat_data is not None
	except AssertionError:
		return

	if tid not in context.chat_data:
		tweet = await get_tweet(tweet_id = tid, shout = True, recursive = 1)
		if not tweet:
			await message.reply_markdown_v2(disMarkdown(f"*未能处理你的请求*\nTweet ID: {tid}"))
			return
		context.chat_data[tid] = tweet, message
	if mode == "NO":
		await message.delete()
		return
	tweet, original = cast(tuple[Tweet, Message], context.chat_data[tid])
	if not mode.startswith("_"):
		await message.edit_text("请稍候……")
	await callback_main(message, original, query.from_user, tweet, mode)

async def callback_main(message: Message, original: Message,
	user: User, tweet: Tweet, mode: str) -> None:
	match original.forward_origin:
		case MessageOriginUser(sender_user = usr):
			fwd = usr
		case MessageOriginHiddenUser(sender_user_name = usr_name):
			fwd = usr_name
		case _:
			fwd = None
	text = output(tweet, from_user = mode != "ALL" or user, forward_user = fwd)
	kwargs = generate_kwargs(tweet, text)
	if mode == "ALL" and (rply := original.reply_to_message):
		kwargs["reply_to_message_id"] = rply.id
	try:
		sent = await match_send(message, kwargs, reply_to_id = original.id if mode.startswith("_") else None)
	except Exception as exp:
		logging.error(f"[发送推文失败] {tweet.id}: {exp!r}")
		await message.reply_markdown_v2(disMarkdown(f"*未能发送你的请求*\nTweet ID: {tweet.id}"))

	if message is not original and not mode.startswith("_"):
		await message.delete()
	if mode.startswith("_"):
		new_buttons = []
		if k := message.reply_markup:
			row = k.inline_keyboard[0]
			new_buttons.extend(b for b in row if tweet.id not in str(b.callback_data))
		new_markup = InlineKeyboardMarkup([new_buttons]) if new_buttons else None
		await message.edit_reply_markup(new_markup)
	try:
		assert mode == "ALL", "no deletion required"
		assert sent and sent.from_user
		admins = await message.chat.get_administrators()
		admin = next(a for a in admins if a.user.id == sent.from_user.id)
		assert isinstance(admin, ChatMemberAdministrator), "not an administrator"
		assert admin.can_delete_messages, "cant be deleted message"
		await original.delete()
	except Exception:
		pass

command_handler = CommandHandler(["x", "twitter"], entry)
group_handlers = [MessageHandler(filters.Regex(url_regex), entry),
	CallbackQueryHandler(callback, pattern = "^TWEET")]