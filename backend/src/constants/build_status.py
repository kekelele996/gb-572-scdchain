"""Build run lifecycle — shared with frontend/src/constants/buildStatus.ts."""
from enum import StrEnum


class BuildStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RunMode(StrEnum):
    FULL = "full"        # 全量重建（当前唯一模式）
    VALIDATE = "validate"


BUILD_STATUS_LABELS: dict[str, str] = {
    BuildStatus.PENDING: "排队中",
    BuildStatus.RUNNING: "构建中",
    BuildStatus.SUCCEEDED: "已完成",
    BuildStatus.FAILED: "失败",
}
