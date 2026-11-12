"""Customer dimension attribute catalogue (dimension design page reads this)."""
from .customer_level import LEVEL_ORDER
from .normalization import NormalizationStrategy


class AttributeType:
    TEXT = "text"
    ENUM = "enum"
    CODE = "code"
    PHONE = "phone"


ATTRIBUTES: list[dict] = [
    {
        "key": "customer_level",
        "label": "客户等级",
        "data_type": AttributeType.ENUM,
        "unit": "",
        "enum_values": list(LEVEL_ORDER),
        "description": "监管报送口径的当时客户等级，变更需要留链",
        "default_normalization": NormalizationStrategy.DIRECT,
    },
    {
        "key": "full_name",
        "label": "客户姓名",
        "data_type": AttributeType.TEXT,
        "unit": "",
        "enum_values": [],
        "description": "三系统姓名存在同音字差异，按拼音收敛",
        "default_normalization": NormalizationStrategy.NAME_HOMOPHONE,
    },
    {
        "key": "mobile",
        "label": "手机号",
        "data_type": AttributeType.PHONE,
        "unit": "",
        "enum_values": [],
        "description": "上游分隔符写法不统一，比较前去分隔符",
        "default_normalization": NormalizationStrategy.PHONE_DIGITS,
    },
    {
        "key": "org_code",
        "label": "归属机构",
        "data_type": AttributeType.CODE,
        "unit": "",
        "enum_values": ["BJ01", "SH02", "GZ03", "CD04"],
        "description": "机构编码/名称多套写法，按映射表归一",
        "default_normalization": NormalizationStrategy.ORG_CODE_MAP,
    },
    {
        "key": "city",
        "label": "所在城市",
        "data_type": AttributeType.TEXT,
        "unit": "",
        "enum_values": [],
        "description": "保单签发城市",
        "default_normalization": NormalizationStrategy.DIRECT,
    },
    {
        "key": "channel",
        "label": "投保渠道",
        "data_type": AttributeType.ENUM,
        "unit": "",
        "enum_values": ["个险", "银保", "团险"],
        "description": "渠道口径由业务侧维护，不参与拉链变更判定（忽略列）",
        "default_normalization": NormalizationStrategy.DIRECT,
    },
]

ATTRIBUTE_KEYS = tuple(attribute["key"] for attribute in ATTRIBUTES)
CHANGE_EXCLUDED_ATTRS = ("channel",)
