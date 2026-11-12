export const CONFLICT_STATUS_LABELS: Record<string, string> = {
  open: '待裁决',
  resolved: '已裁决',
  manual: '人工覆盖',
};

export const VERDICT_LABELS: Record<string, string> = {
  normalized_equal: '归一后一致',
  similar: '同音/近似',
  conflict: '真实冲突',
};

export const NORMALIZATION_LABELS: Record<string, string> = {
  direct: '原样比较',
  phone_digits: '手机号去分隔符',
  org_code_map: '机构编码映射',
  name_homophone: '姓名同音比对',
};
