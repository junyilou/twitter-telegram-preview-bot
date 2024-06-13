# twitter-telegram-preview-bot

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

## 环境

你需要使用 Python 3.12 及以上版本才能运行此代码。

### 依赖

* [python-telegram-bot](): Python Telegram Bot 包装
* [twitter-api-client](https://github.com/trevorhobenshield/twitter-api-client): Python Twitter GraphQL API 包装

通过 pypi 安装全部依赖:

``` shell
python3.12 -m pip install -r requirements.txt
```

## 使用

请先通过 [@BotFather](https://t.me/botfather) 申请你自己的 Bot，将 Token 填写在 [BotApp.py](BotApp.py) 中。

而后参考 [twitter-api-client](https://github.com/trevorhobenshield/twitter-api-client) 给出的方法，登录你的 Twitter 账号，保存 Cookies 到 `bot-scraper.cookies` 文件。在 [modules/tweet.py](modules/tweet.py) 有一个简单的登录函数实现 `login()`。

然后运行即可。如需指定功能白名单，可参考 [twitterBot/permission.py](twitterBot/permission.py)。