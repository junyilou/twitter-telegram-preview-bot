# twitter-telegram-preview-bot

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)



一个推文预览 Telegram 消息生成工具。完整功能已在 [@kotorixbot](https://t.me/kotorixbot) 中实现。

## 效果图

#### 多图相册

![多图相册](images/album.png)

#### 视频消息

![视频消息](images/video.png)

#### 内联消息

![内联消息](images/inline.png)



## 搭建使用

已改为使用 [dylanpdx/BetterTwitFix](https://github.com/dylanpdx/BetterTwitFix) 提供的接口进行实现，相较原先的版本几乎无功能性损失，同时提供更高的稳定性，也无需再安装 Twitter 相关的 PyPI 依赖。

你需要使用 Python 3.12 及以上版本才能运行此代码。

* [aiohttp](https://github.com/aio-libs/aiohttp): 异步网络请求
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot): Python Telegram Bot 包装

通过 pypi 安装全部依赖:

``` shell
python3.12 -m pip install -r requirements.txt
```

通过 [@BotFather](https://t.me/botfather) 申请你自己的 Bot，然后将 Token 填写在 [BotApp.py](BotApp.py) 中。
