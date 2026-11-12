"""Customer level scale — shared with frontend/src/constants/customerLevel.ts."""
from enum import StrEnum


class CustomerLevel(StrEnum):
    SILVER = "银卡"
    GOLD = "金卡"
    PLATINUM = "白金卡"
    DIAMOND = "钻石卡"


LEVEL_ORDER = (
    CustomerLevel.SILVER.value,
    CustomerLevel.GOLD.value,
    CustomerLevel.PLATINUM.value,
    CustomerLevel.DIAMOND.value,
)
