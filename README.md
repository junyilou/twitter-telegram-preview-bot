# twitter-telegram-preview-bot

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

##### 更新

已改为使用 [dylanpdx/BetterTwitFix](https://github.com/dylanpdx/BetterTwitFix) 提供的接口进行实现，相较原先的版本几乎无功能性损失，同时提供更高的稳定性，也无需再安装 Twitter 相关的 PyPI 依赖。



## 环境

你需要使用 Python 3.12 及以上版本才能运行此代码。

### 依赖

* [aiohttp](https://github.com/aio-libs/aiohttp): 异步网络请求
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot): Python Telegram Bot 包装
* ~~[twitter-api-client](https://github.com/trevorhobenshield/twitter-api-client): Python Twitter GraphQL API 包装~~

通过 pypi 安装全部依赖:

``` shell
python3.12 -m pip install -r requirements.txt
```

## 使用

请先通过 [@BotFather](https://t.me/botfather) 申请你自己的 Bot，将 Token 填写在 [BotApp.py](BotApp.py) 中。

然后运行即可。如需指定功能白名单，可参考 [twitterBot/permission.py](twitterBot/permission.py)。



#### 原始版本（不再需要）

参考 [twitter-api-client](https://github.com/trevorhobenshield/twitter-api-client) 给出的方法，登录你的 Twitter 账号，保存 Cookies 到 `bot-scraper.cookies` 文件。

在 [modules/tweet.py](modules/tweet.py) 有一个简单的登录函数实现 `login`。这需要用到 `auth_token` 和 `ct0` 两个 Cookies 值，我们强烈建议使用普通浏览器登陆一个小号帐号，然后从浏览器找到这两个值，而不是尝试用代码进行登录。一个示例 `bot-scraper.cookies` 文件为如下的 JSON 内容：

```json
{
  "auth_token": "29e02bd89a8de3c454d5f68d65413f9042980fdb",
  "ct0": "a07828539fdae85639bd8af00f286cd5abe6239d5ba128a5a78c805b72e8b27708d05b2f8ea1237448af81e4f086ac641b3726c169835b1bb90f63466007697856e90441477aa46f47f20311e9916709"
}
```

