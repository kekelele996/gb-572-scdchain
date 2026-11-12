"""Deterministic demo fixture for scdchain — pure data, no database imports.

The whole scenario is a fixed function of SHA-256 derived seeds, so the seed
script can be re-run any number of times and produce byte-identical output:

    3 source systems · 180 customer keys · 5 daily snapshots (900 rows)
    24 cross-source conflict windows · 30 level changes (210 zipper chains)
    2 build runs · 3 role accounts
"""
from __future__ import annotations

import hashlib
import random
from datetime import date, datetime

BRAND = "scdchain"
SNAPSHOT_DATES: tuple[date, ...] = (
    date(2026, 11, 1),
    date(2026, 11, 2),
    date(2026, 11, 3),
    date(2026, 11, 4),
    date(2026, 11, 5),
)
CUSTOMER_COUNT = 180
DUPLICATE_KEYS = tuple(range(100, 124))
MISSING_DAY_KEYS = tuple(range(124, 148))
CHANGE_KEY_START = 30
CHANGE_KEY_COUNT = 30
LATE_KEYS = tuple(range(40, 46))
ASOF_DEMO_INDEX = 59  # CUST-0060: 银卡 -> 金卡 observed 2026-11-05 (effective 2026-11-06)
OVERRIDE_EFFECTIVE = date(2026, 11, 6)

SOURCES: list[dict] = [
    {
        "code": "core_policy",
        "name": "核心保单系统",
        "system_type": "policy-core",
        "description": "2019 年老核心，客户主档与保单等级的唯一权威口径",
        "contact_owner": "周慕云（核心平台组）",
        "snapshot_time": "02:00",
        "trust_level": 3,
    },
    {
        "code": "member_center",
        "name": "会员中心",
        "system_type": "crm",
        "description": "2022 年上线的会员权益系统，等级与机构归属常被运营手工调整",
        "contact_owner": "许清和（会员运营）",
        "snapshot_time": "03:00",
        "trust_level": 2,
    },
    {
        "code": "service_desk",
        "name": "客服工单系统",
        "system_type": "ticketing",
        "description": "工单里由坐席补录的客户联系信息，手机号与姓名写法最不规范",
        "contact_owner": "宋知远（客服运营）",
        "snapshot_time": "04:00",
        "trust_level": 1,
    },
]

PRIORITY = ("core_policy", "member_center", "service_desk")

RULE_SPECS: list[dict] = [
    {
        "attribute_key": "customer_level",
        "display_name": "客户等级",
        "data_type": "enum",
        "source_priority": list(PRIORITY),
        "normalization": "direct",
        "exclude_from_change": False,
    },
    {
        "attribute_key": "full_name",
        "display_name": "客户姓名",
        "data_type": "text",
        "source_priority": list(PRIORITY),
        "normalization": "name_homophone",
        "exclude_from_change": False,
    },
    {
        "attribute_key": "mobile",
        "display_name": "手机号",
        "data_type": "phone",
        "source_priority": list(PRIORITY),
        "normalization": "phone_digits",
        "exclude_from_change": False,
    },
    {
        "attribute_key": "org_code",
        "display_name": "归属机构",
        "data_type": "code",
        "source_priority": list(PRIORITY),
        "normalization": "org_code_map",
        "exclude_from_change": False,
    },
    {
        "attribute_key": "city",
        "display_name": "所在城市",
        "data_type": "text",
        "source_priority": list(PRIORITY),
        "normalization": "direct",
        "exclude_from_change": False,
    },
    {
        "attribute_key": "channel",
        "display_name": "投保渠道",
        "data_type": "enum",
        "source_priority": list(PRIORITY),
        "normalization": "direct",
        "exclude_from_change": True,  # ignored column: channel edits must not open a chain
    },
]

LEVELS = ("银卡", "金卡", "白金卡", "钻石卡")
ORGS = ("BJ01", "SH02", "GZ03", "CD04")
CITY_BY_ORG = {"BJ01": "北京", "SH02": "上海", "GZ03": "广州", "CD04": "成都"}
CHANNELS = ("个险", "银保", "团险")
SURNAMES = "王李张刘陈杨赵黄周吴徐孙马朱胡郭何高林罗"
GIVENS = [
    "嘉禾", "子墨", "雨桐", "思远", "若溪", "振宇", "晚晴", "书言", "宁远", "云舒",
    "知远", "明杰", "静婷", "欣悦", "俊伟", "宇宁", "佳和", "子言", "雨欣", "嘉宁",
]

HOMOPHONE_BASE = {"陈嘉禾": "陈佳禾", "李雨桐": "李羽彤", "周墨言": "周默言", "吴若溪": "吴若希"}
HOMOPHONE_KEYS = tuple(range(114, 118))
TRUE_LEVEL_KEYS = tuple(range(118, 121))
TRUE_ORG_KEYS = tuple(range(121, 124))


def _rng(*parts: object) -> random.Random:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def business_key(index: int) -> str:
    return f"CUST-{index + 1:04d}"


def _base_level(index: int) -> str:
    return LEVELS[(index * 3) % 4]


def _change_day(index: int) -> date | None:
    position = index - CHANGE_KEY_START
    if position < 0 or position >= CHANGE_KEY_COUNT:
        return None
    if position < 10:
        return date(2026, 11, 3)
    if position < 20:
        return date(2026, 11, 4)
    return date(2026, 11, 5)


def _new_level(index: int) -> str:
    if index == ASOF_DEMO_INDEX:
        return "金卡"
    base = _base_level(index)
    return LEVELS[(LEVELS.index(base) + 1) % len(LEVELS)]


def build_customers() -> list[dict]:
    customers: list[dict] = []
    for index in range(CUSTOMER_COUNT):
        rng = _rng("customer", index)
        if index in HOMOPHONE_KEYS:
            name = list(HOMOPHONE_BASE)[index - HOMOPHONE_KEYS[0]]
        else:
            name = SURNAMES[index % len(SURNAMES)] + GIVENS[(index * 7) % len(GIVENS)]
        mobile = f"13{index % 10}{(index * 37) % 100000000:08d}"
        org = ORGS[index % len(ORGS)]
        level = _base_level(index)
        if index == ASOF_DEMO_INDEX:
            level = "银卡"
        primary_source = "core_policy" if index in DUPLICATE_KEYS else PRIORITY[index % 3]
        customers.append(
            {
                "index": index,
                "business_key": business_key(index),
                "full_name": name,
                "mobile": mobile,
                "org_code": org,
                "customer_level": level,
                "city": CITY_BY_ORG[org],
                "channel": CHANNELS[(index * 5) % len(CHANNELS)],
                "primary_source": primary_source,
                "change_date": _change_day(index),
                "new_level": _new_level(index) if _change_day(index) else "",
                "rng_hint": f"{rng.randint(0, 9999):04d}",
            }
        )
    return customers


def _level_at(customer: dict, snapshot_date: date) -> str:
    change_date = customer["change_date"]
    if change_date is not None and snapshot_date >= change_date:
        return customer["new_level"]
    return customer["customer_level"]


def _raw_attributes(customer: dict, snapshot_date: date) -> dict:
    return {
        "full_name": customer["full_name"],
        "mobile": customer["mobile"],
        "org_code": customer["org_code"],
        "customer_level": _level_at(customer, snapshot_date),
        "city": customer["city"],
        "channel": customer["channel"],
    }


def _duplicate_variant(customer: dict, raw: dict) -> dict:
    variant = dict(raw)
    index = customer["index"]
    if index <= 108:
        digits = raw["mobile"]
        variant["mobile"] = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif index <= 113:
        variant["org_code"] = f"ORG-{raw['org_code']}"
    elif index in HOMOPHONE_KEYS:
        variant["full_name"] = HOMOPHONE_BASE[customer["full_name"]]
    elif index in TRUE_LEVEL_KEYS:
        current = raw["customer_level"]
        variant["customer_level"] = LEVELS[(LEVELS.index(current) + 2) % len(LEVELS)]
    else:
        current = raw["org_code"]
        variant["org_code"] = ORGS[(ORGS.index(current) + 1) % len(ORGS)]
    return variant


def build_snapshots(customers: list[dict]) -> list[dict]:
    trust_by_source = {source["code"]: source["trust_level"] for source in SOURCES}
    snapshots: list[dict] = []
    for customer in customers:
        index = customer["index"]
        for snapshot_date in SNAPSHOT_DATES:
            if index in MISSING_DAY_KEYS and snapshot_date == date(2026, 11, 2):
                continue
            raw = _raw_attributes(customer, snapshot_date)
            ingested_at = datetime(snapshot_date.year, snapshot_date.month, snapshot_date.day, 6, 0, 0)
            is_late = False
            if index in LATE_KEYS and snapshot_date == date(2026, 11, 4):
                ingested_at = datetime(2026, 11, 6, 9, 0, 0)
                is_late = True
            source_code = customer["primary_source"]
            snapshots.append(
                {
                    "business_key": customer["business_key"],
                    "source_code": source_code,
                    "snapshot_date": snapshot_date,
                    "attributes": raw,
                    "ingested_at": ingested_at,
                    "trust": trust_by_source[source_code],
                    "is_late": is_late,
                    "batch_tag": "daily-full" if not is_late else "late-replay",
                }
            )
        if index in DUPLICATE_KEYS:
            snapshot_date = date(2026, 11, 5)
            raw = _raw_attributes(customer, snapshot_date)
            snapshots.append(
                {
                    "business_key": customer["business_key"],
                    "source_code": "member_center",
                    "snapshot_date": snapshot_date,
                    "attributes": _duplicate_variant(customer, raw),
                    "ingested_at": datetime(2026, 11, 5, 8, 0, 0),
                    "trust": trust_by_source["member_center"],
                    "is_late": False,
                    "batch_tag": "member-day-close",
                }
            )
    return snapshots


def build_dataset() -> dict:
    customers = build_customers()
    snapshots = build_snapshots(customers)
    return {
        "brand": BRAND,
        "sources": SOURCES,
        "customers": customers,
        "snapshots": snapshots,
        "rule_specs": RULE_SPECS,
        "snapshot_dates": [day.isoformat() for day in SNAPSHOT_DATES],
        "expected": {
            "sources": len(SOURCES),
            "customers": CUSTOMER_COUNT,
            "snapshots": len(snapshots),
            "conflict_windows": len(DUPLICATE_KEYS),
        },
    }
