export type Role = 'admin' | 'modeler' | 'auditor';

export interface User {
  id: number;
  email: string;
  display_name: string;
  role: Role;
}

export interface Paged<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiErrorBody {
  error?: { code?: string; message?: string; request_id?: string };
}

export interface InvariantCheck {
  passed: number;
  total: number;
  failed_keys: string[];
}

export interface Invariants {
  uniqueness: InvariantCheck;
  overlap: InvariantCheck;
  gap: InvariantCheck;
  order: InvariantCheck;
  all_passed: boolean;
}
