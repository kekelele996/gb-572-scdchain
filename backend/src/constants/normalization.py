"""Attribute normalisation strategies — shared with frontend/src/constants/normalization.ts."""
from enum import StrEnum


class NormalizationStrategy(StrEnum):
    DIRECT = "direct"                 # 原样比较
    PHONE_DIGITS = "phone_digits"     # 手机号去分隔符 / 去 +86
    ORG_CODE_MAP = "org_code_map"     # 机构编码映射（ORG-BJ01 / BJ01 / 华北一区 -> BJ01）
    NAME_HOMOPHONE = "name_homophone" # 姓名按拼音同音比较


NORMALIZATION_LABELS: dict[str, str] = {
    NormalizationStrategy.DIRECT: "原样比较",
    NormalizationStrategy.PHONE_DIGITS: "手机号去分隔符",
    NormalizationStrategy.ORG_CODE_MAP: "机构编码映射",
    NormalizationStrategy.NAME_HOMOPHONE: "姓名同音比对",
}
