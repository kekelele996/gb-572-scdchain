export const BUILD_STATUS_LABELS: Record<string, string> = {
  pending: '排队中',
  running: '构建中',
  succeeded: '已完成',
  failed: '失败',
};

export const BUILD_STATUS_TONE: Record<string, string> = {
  pending: 'seal--neutral',
  running: 'seal--warn',
  succeeded: 'seal--ok',
  failed: 'seal--bad',
};
