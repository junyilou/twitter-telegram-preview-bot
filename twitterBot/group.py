import logging
from typing import cast

from telegram import (ChatMemberAdministrator, InlineKeyboardButton,
                      InlineKeyboardMarkup, Message, MessageOriginHiddenUser,
                      MessageOriginUser, Update, User)
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

# from modules.tweet import get_tweet
from modules.util import disMarkdown
from modules.vxtwitter import get_tweet

from .models import TweetModel, generate_kwargs, match_send, url_regex
from .permission import whitelist


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
			tweet = await get_tweet(tweet_id = tid, shout = True)
			assert tweet
			model = TweetModel(tweet)
		except Exception as exp:
			logging.error(f"[处理推文失败] {tid}: {exp!r}")
			await message.reply_markdown_v2(disMarkdown(f"*未能处理你的请求*\nTweet ID: {tid}"))
			continue
		if is_private:
			await entry_manual(message, model)
		else:
			await entry_group(message, model, context)

async def entry_group(message: Message, model: TweetModel, context: ContextTypes.DEFAULT_TYPE) -> None:
	assert context.chat_data is not None and message.text is not None
	text = f"*要生成推文预览吗？*\n\n{model.preview}"
	keyboard = [[InlineKeyboardButton("生成", callback_data = f"TWEET YES {model.tweet.id}"),
		InlineKeyboardButton("忽略", callback_data = f"TWEET NO {model.tweet.id}")]]
	if message.forward_origin or " " not in message.text.strip():
		keyboard[0].insert(0, InlineKeyboardButton("生成并删除", callback_data = f"TWEET ALL {model.tweet.id}"))
	await message.reply_markdown_v2(text, disable_web_page_preview = True,
		reply_markup = InlineKeyboardMarkup(keyboard), quote = False)
	context.chat_data[model.tweet.id] = model, message

async def entry_manual(message: Message, model: TweetModel) -> None:
	assert message.from_user is not None
	await callback_main(message, message, message.from_user, model, "YES")

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
		await message.reply_markdown_v2(disMarkdown(f"*请重新发起你的请求*\nTweet ID: {tid}"))
		await message.edit_reply_markup()
		return
	if mode == "NO":
		await message.delete()
		return
	model, original = cast(tuple[TweetModel, Message], context.chat_data[tid])
	await message.edit_text("请稍候……")
	await callback_main(message, original, query.from_user, model, mode)

async def callback_main(message: Message, original: Message,
	user: User, model: TweetModel, mode: str) -> None:
	match original.forward_origin:
		case MessageOriginUser(sender_user = usr):
			fwd = usr
		case MessageOriginHiddenUser(sender_user_name = usr_name):
			fwd = usr_name
		case _:
			fwd = None
	text = model.output_group(from_user = mode != "ALL" or user, forward_user = fwd)
	kwargs = generate_kwargs(model.tweet, text)
	if mode == "ALL" and (rply := original.reply_to_message):
		kwargs["reply_to_message_id"] = rply.id
	try:
		sent = await match_send(message, kwargs)
	except Exception as exp:
		logging.error(f"[发送推文失败] {model.tweet.id}: {exp!r}")
		await message.reply_markdown_v2(disMarkdown(f"*未能发送你的请求*\nTweet ID: {model.tweet.id}"))

	if message is not original:
		await message.delete()
	try:
		assert mode == "ALL", "no deletion required"
		assert sent and sent.from_user
		admins = await message.chat.get_administrators()
		admin = next(a for a in admins if a.user.id == sent.from_user.id)
		assert isinstance(admin, ChatMemberAdministrator), "not an administrator"
		assert admin.can_delete_messages, "cant be deleted message"
		await original.delete()
	except:
		pass

command_handler = CommandHandler(["x", "twitter"], entry)
group_handlers = [MessageHandler(filters.Chat(chat_id = whitelist, allow_empty = True) & filters.Regex(url_regex), entry),
	CallbackQueryHandler(callback, pattern = "^TWEET")]