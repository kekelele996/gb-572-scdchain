export const LEVELS = ['银卡', '金卡', '白金卡', '钻石卡'] as const;

export const LEVEL_TONE: Record<string, string> = {
  银卡: 'seal--neutral',
  金卡: 'seal--warn',
  白金卡: 'seal--navy',
  钻石卡: 'seal--ok',
};
