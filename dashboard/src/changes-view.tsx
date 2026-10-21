// 变更记录：服务端分页，打开与刷新时请求；不做定时轮询。
import { Button, Card, Table, Tag, message } from "antd";
import type { TableProps } from "antd";
import { useEffect, useState } from "react";

import { STATUS_LABELS, TYPE_LABELS, formatTime } from "./api";
import type { ChangeRecord, ChangesResponse } from "./api";
import { apiGet } from "./bridge";

const PAGE_SIZE = 20;
const STATUS_PAGE_BASE = "https://status.deepseek.com";

function statusColor(status: string): string {
  return status === "resolved" || status === "completed" ? "green" : "orange";
}

export default function ChangesView() {
  const [rows, setRows] = useState<ChangeRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  async function load(target: number) {
    setLoading(true);
    try {
      const data = await apiGet<ChangesResponse>("history", {
        page: target,
        size: PAGE_SIZE,
      });
      setRows(data.changes);
      setTotal(data.total);
      setPage(data.page);
    } catch (error) {
      message.error(error instanceof Error ? error.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(1);
  }, []);

  const columns: TableProps<ChangeRecord>["columns"] = [
    {
      title: "采集时间",
      dataIndex: "fetched_at",
      width: 180,
      render: (value: string) => formatTime(value),
    },
    {
      title: "事件",
      dataIndex: "title",
      render: (value: string, record: ChangeRecord) => (
        <a
          href={`${STATUS_PAGE_BASE}/incidents/${record.change_id}`}
          target="_blank"
          rel="noreferrer"
        >
          {value || "未命名事件"}
        </a>
      ),
    },
    {
      title: "类型",
      dataIndex: "change_type",
      width: 110,
      render: (value: string) => TYPE_LABELS[value] ?? value,
    },
    {
      title: "状态",
      dataIndex: "status",
      width: 110,
      render: (value: string) => (
        <Tag color={statusColor(value)}>{STATUS_LABELS[value] ?? value}</Tag>
      ),
    },
  ];

  return (
    <Card
      title="变更记录"
      extra={
        <Button onClick={() => void load(page)} loading={loading}>
          刷新
        </Button>
      }
    >
      <Table
        rowKey="id"
        columns={columns}
        dataSource={rows}
        loading={loading}
        pagination={{
          current: page,
          pageSize: PAGE_SIZE,
          total,
          showSizeChanger: false,
          showTotal: (count) => `共 ${count} 条`,
          onChange: (next) => void load(next),
        }}
      />
    </Card>
  );
}
