import type { Role } from '@/types/api';

export const ROLE_LABELS: Record<Role, string> = {
  admin: '建模负责人',
  modeler: '建模工程师',
  auditor: '审计只读',
};

export const ROLE_SCOPE: Record<Role, string> = {
  admin: '维度定义 / 合并规则 / 发布',
  modeler: '跑构建 / 处理冲突 / 校验',
  auditor: '任意时点回溯 / 导出（只读）',
};
