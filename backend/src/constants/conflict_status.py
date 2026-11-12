"""Conflict lifecycle and resolution strategies — shared with frontend/src/constants/conflictStatus.ts."""
from enum import StrEnum


class ConflictStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    MANUAL = "manual"


class ResolutionStrategy(StrEnum):
    PRIORITY = "priority"                 # 构建期按 MergeRule 源优先级直接取用
    PHONE_DIGITS = "phone_digits"         # 归一后相等，自动收敛
    ORG_CODE_MAP = "org_code_map"         # 机构编码映射后相等，自动收敛
    NAME_HOMOPHONE = "name_homophone"     # 同音姓名，自动收敛到高优先源
    CANDIDATE = "candidate"               # 人工在候选值中裁定
    MANUAL = "manual"                     # 人工覆盖（可填非候选值）


CONFLICT_STATUS_LABELS: dict[str, str] = {
    ConflictStatus.OPEN: "待裁决",
    ConflictStatus.RESOLVED: "已裁决",
    ConflictStatus.MANUAL: "人工覆盖",
}

STRATEGY_LABELS: dict[str, str] = {
    ResolutionStrategy.PRIORITY: "源优先级",
    ResolutionStrategy.PHONE_DIGITS: "手机号归一",
    ResolutionStrategy.ORG_CODE_MAP: "机构编码映射",
    ResolutionStrategy.NAME_HOMOPHONE: "姓名同音",
    ResolutionStrategy.CANDIDATE: "候选裁定",
    ResolutionStrategy.MANUAL: "人工覆盖",
}
