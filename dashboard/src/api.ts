// 页面共用的接口类型与展示映射；字段与后端 Web API 返回保持一致。
export type StatusEvent = {
  change_id: number;
  change_type: string;
  title: string;
  status: string;
  link: string;
};

export type Snapshot = {
  status: "normal" | "abnormal";
  fetched_at: string;
  events: StatusEvent[];
};

export type StatusResponse = {
  enabled: boolean;
  snapshot: Snapshot | null;
};

export type Settings = {
  enabled: boolean;
  poll_interval_seconds: number;
  notify_enabled: boolean;
  history_retention_days: number;
  display_timezone: string;
};

export type SettingsResponse = {
  settings: Settings;
};

export type Subscription = {
  id: number;
  session: string;
  note: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type SubscriptionsResponse = {
  subscriptions: Subscription[];
};

export type ChangeRecord = {
  id: number;
  change_id: number;
  change_type: string;
  title: string;
  status: string;
  fetched_at: string;
};

export type ChangesResponse = {
  changes: ChangeRecord[];
  total: number;
  page: number;
  size: number;
};

export const STATUS_LABELS: Record<string, string> = {
  investigating: "调查中",
  identified: "已定位",
  monitoring: "观察中",
  scheduled: "已排期",
  ongoing: "进行中",
  resolved: "已解决",
  completed: "已完成",
};

export const TYPE_LABELS: Record<string, string> = {
  incident: "故障",
  maintenance: "计划维护",
};

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleString("zh-CN", { hour12: false });
}

export function isUnfinished(event: StatusEvent): boolean {
  return event.status !== "resolved" && event.status !== "completed";
}
