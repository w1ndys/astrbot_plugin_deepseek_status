// 概览卡：监控关闭、无数据、正常、非正常四种展示。
import { Alert, Card, List, Tag, Typography } from "antd";

import { STATUS_LABELS, TYPE_LABELS, formatTime, isUnfinished } from "./api";
import type { Snapshot } from "./api";

type Props = {
  enabled: boolean;
  snapshot: Snapshot | null;
};

export default function StatusCard({ enabled, snapshot }: Props) {
  if (!enabled) {
    return <Alert type="info" showIcon message="监控已关闭" description="在下方配置中启用后才会采集状态。" />;
  }
  if (!snapshot) {
    return (
      <Alert
        type="warning"
        showIcon
        message="暂无数据"
        description="监控刚启动，首次采集成功后这里会显示状态。"
      />
    );
  }
  const unfinished = snapshot.events.filter(isUnfinished);
  const normal = unfinished.length === 0;
  return (
    <Card
      size="small"
      title="当前状态"
      extra={<Tag color={normal ? "green" : "red"}>{normal ? "一切运行正常" : `${unfinished.length} 条未结束事件`}</Tag>}
    >
      <Typography.Paragraph type="secondary">
        采集时间：{formatTime(snapshot.fetched_at)}
      </Typography.Paragraph>
      {unfinished.length > 0 && (
        <List
          size="small"
          dataSource={unfinished}
          renderItem={(event) => (
            <List.Item>
              <List.Item.Meta
                title={
                  <a href={event.link} target="_blank" rel="noreferrer">
                    {event.title || "未命名事件"}
                  </a>
                }
                description={`${TYPE_LABELS[event.change_type] ?? event.change_type} / ${
                  STATUS_LABELS[event.status] ?? event.status
                }`}
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
}
