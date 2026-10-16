import os
import re
import sys
from urllib.parse import urlparse, unquote

import requests

INFO_URL = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/info"
SIGN_URL = "https://drive-m.quark.cn/1/clouddrive/capacity/growth/sign"
TIMEOUT = 20


def parse_accounts(raw):
    accounts = []
    for block in re.split(r"\n|&&", raw or ""):
        block = block.strip()
        if not block:
            continue
        item = {}
        for part in block.split(";"):
            part = part.strip()
            if "=" in part:
                key, value = part.split("=", 1)
                item[key.strip()] = value.strip()
        # New format: user=...; url=https://...?...&kps=...&sign=...&vcode=...
        if item.get("url"):
            # unquote() deliberately preserves literal '+' characters; parse_qs()
            # would turn '+' into a space and can corrupt newer Quark credentials.
            query = {}
            for pair in urlparse(item["url"]).query.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    query[unquote(key)] = unquote(value)
            for key in ("kps", "sign", "vcode"):
                if not item.get(key) and query.get(key):
                    item[key] = query[key]
        if not all(item.get(key) for key in ("kps", "sign", "vcode")):
            raise ValueError(
                "账号配置缺少 kps/sign/vcode；请检查 COOKIE_QUARK，或重新抓取完整签到 URL。"
            )
        accounts.append(item)
    if not accounts:
        raise ValueError("未读取到账号，请检查 GitHub Secret COOKIE_QUARK。")
    return accounts


def request_json(method, url, **kwargs):
    response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"接口返回的不是有效 JSON（HTTP {response.status_code}）") from exc
    return data


def params_for(account):
    return {
        "pr": "ucpro",
        "fr": "android",
        "kps": account["kps"],
        "sign": account["sign"],
        "vcode": account["vcode"],
    }


def format_bytes(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} PB"


def sign_account(account, index):
    user = account.get("user") or f"账号 {index}"
    params = params_for(account)
    info = request_json("GET", INFO_URL, params=params)
    growth = info.get("data")
    if not growth:
        raise RuntimeError(f"获取成长信息失败：{info.get('message') or info.get('msg') or '接口未返回 data'}")

    vip = "88VIP" if growth.get("88VIP") else "普通用户"
    cap_sign = growth.get("cap_sign") or {}
    total = format_bytes(growth.get("total_capacity", 0))
    lines = [f"{vip} {user}", f"网盘总容量：{total}"]

    if cap_sign.get("sign_daily"):
        reward = cap_sign.get("sign_daily_reward", 0)
        lines.append(f"已签到：今日奖励 {format_bytes(reward)}")
        return "\n".join(lines)

    result = request_json(
        "POST",
        SIGN_URL,
        params=params,
        json={"sign_cyclic": True},
    )
    data = result.get("data")
    if not data:
        raise RuntimeError(f"签到失败：{result.get('message') or result.get('msg') or '接口未返回 data'}")

    reward = data.get("sign_daily_reward", 0)
    lines.append(f"签到成功：今日奖励 {format_bytes(reward)}")
    return "\n".join(lines)


def main():
    raw = os.environ.get("COOKIE_QUARK", "")
    if not raw.strip():
        print("❌ 未设置 GitHub Secret COOKIE_QUARK")
        return 2

    try:
        accounts = parse_accounts(raw)
    except Exception as exc:
        print(f"❌ 配置错误：{exc}")
        return 2

    print(f"检测到 {len(accounts)} 个夸克账号")
    failures = 0
    for index, account in enumerate(accounts, start=1):
        try:
            print(f"\n[{index}/{len(accounts)}] {sign_account(account, index)}")
        except Exception as exc:
            failures += 1
            print(f"\n❌ 第 {index} 个账号（{account.get('user') or '未命名'}）失败：{exc}")

    if failures:
        print(f"\n签到结束：{failures} 个账号失败。请检查凭证或接口状态。")
        return 1
    print("\n签到结束：所有账号均已签到或签到成功。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
