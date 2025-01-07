from datetime import datetime
from typing import Any, Optional

import aiohttp

browser_agent = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
	"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"}

def disMarkdown(text: str, wrap: str = "", extra: str = "") -> str:
	signs = "\\|_{}[]()#@+-.!=<>~" + extra
	text = text.translate({ord(s): f"\\{s}" for s in signs})
	return wrap + text + wrap[::-1]

def time_delta(*,
	seconds: float = 0,
	dt1: datetime = datetime.min,
	dt2: datetime = datetime.min,
	items: Optional[int] = None,
	empty: str = "") -> str:
	ans, base = [], 1
	comp = ((60, "秒"), (60, "分钟"), (24, "小时"), (7, "天"), (0, "周"))
	s = int(abs(seconds or (dt2 - dt1).total_seconds()))
	if not s:
		return empty
	items = items or len(comp)
	for carry, desc in comp:
		if c := s // base:
			if (l := f"{c % carry if carry else c:.0f}") != "0":
				ans.append(f"{l} {desc}")
		base *= carry
		if s < base:
			break
	return " ".join(ans[-1:-1-items:-1])

async def request(url: str, mode: str) -> Any:
	async with aiohttp.ClientSession() as session:
		async with session.get(url, headers = browser_agent) as resp:
			if mode == "json":
				return await resp.json()
			return await resp.text()