from datetime import datetime
from typing import Optional

browser_agent = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"}

def bitsize(integer: int | float, width: int = 8, precision: int = 2, ks: float = 1e3) -> str:
	unit, order = 0, ("B", "KB", "MB", "GB", "TB")
	while integer > ks and unit < len(order) - 1:
		integer /= ks
		unit += 1
	return f"{integer:{width}.{precision}f} {order[unit]:<2}"

def disMarkdown(text: str, wrap: str = "", extra: str = "") -> str:
	signs = "\\`|_{}[]()#@+-.!=<>~" + extra
	text = text.translate({ord(s): f"\\{s}" for s in signs})
	return wrap + text + wrap[::-1]

def timeDelta(*,
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