"""Role enum shared with frontend/src/constants/roles.ts."""
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"      # 建模负责人：维度定义 / 合并规则 / 发布
    MODELER = "modeler"  # 建模工程师：跑构建 / 处理冲突 / 校验
    AUDITOR = "auditor"  # 审计只读：任意时点回溯 + 导出


ROLE_LABELS: dict[str, str] = {
    Role.ADMIN: "建模负责人",
    Role.MODELER: "建模工程师",
    Role.AUDITOR: "审计只读",
}

ALL_ROLES = tuple(role.value for role in Role)
