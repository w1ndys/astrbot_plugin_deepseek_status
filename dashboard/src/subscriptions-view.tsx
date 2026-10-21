// 订阅管理：列表 + 新增/编辑弹窗；启用开关点一下立即保存。
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Table,
  Typography,
  message,
} from "antd";
import type { TableProps } from "antd";
import { useEffect, useState } from "react";

import { formatTime } from "./api";
import type { GroupsResponse, Subscription, SubscriptionsResponse } from "./api";
import { apiGet, apiPost } from "./bridge";

type FormValues = {
  session: string;
  note: string;
  enabled: boolean;
};

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败";
}

export default function SubscriptionsView() {
  const [form] = Form.useForm<FormValues>();
  const [items, setItems] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Subscription | null>(null);
  const [saving, setSaving] = useState(false);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [groups, setGroups] = useState<GroupsResponse["groups"]>([]);
  const [groupLoading, setGroupLoading] = useState(false);
  const [filling, setFilling] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await apiGet<SubscriptionsResponse>("subscriptions");
      setItems(data.subscriptions);
    } catch (error) {
      message.error(errorText(error));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  function openCreate() {
    setEditing(null);
    setGroups([]);
    form.resetFields();
    form.setFieldsValue({ session: "", note: "", enabled: true });
    setModalOpen(true);
  }

  function openEdit(record: Subscription) {
    setEditing(record);
    form.setFieldsValue({
      session: record.session,
      note: record.note,
      enabled: record.enabled,
    });
    setModalOpen(true);
  }

  async function submit() {
    const values = await form.validateFields();
    setSaving(true);
    try {
      if (editing) {
        await apiPost(`subscriptions/${editing.id}/update`, {
          note: values.note,
          enabled: values.enabled,
        });
        message.success("订阅已保存");
      } else {
        await apiPost("subscriptions", values);
        message.success("订阅已新增");
      }
      setModalOpen(false);
      await load();
    } catch (error) {
      message.error(errorText(error));
    } finally {
      setSaving(false);
    }
  }

  async function toggle(record: Subscription, checked: boolean) {
    setTogglingId(record.id);
    try {
      await apiPost(`subscriptions/${record.id}/update`, {
        note: record.note,
        enabled: checked,
      });
      setItems((prev) =>
        prev.map((item) => (item.id === record.id ? { ...item, enabled: checked } : item)),
      );
    } catch (error) {
      message.error(errorText(error));
    } finally {
      setTogglingId(null);
    }
  }

  async function remove(id: number) {
    try {
      await apiPost(`subscriptions/${id}/delete`);
      message.success("订阅已删除");
      await load();
    } catch (error) {
      message.error(errorText(error));
    }
  }

  async function fillNotes() {
    setFilling(true);
    try {
      const data = await apiPost<{ updated: number }>("groups/fill-notes");
      message.success(`已更新 ${data.updated} 条群备注`);
      await load();
    } catch (error) {
      message.error(errorText(error));
    } finally {
      setFilling(false);
    }
  }

  async function loadGroups() {
    setGroupLoading(true);
    try {
      const data = await apiGet<GroupsResponse>("groups");
      setGroups(data.groups);
      // 没有群时给明确提示，避免用户以为按钮坏了
      if (data.groups.length === 0) {
        message.info("aiocqhttp 没有返回任何群");
      }
    } catch (error) {
      message.error(errorText(error));
    } finally {
      setGroupLoading(false);
    }
  }

  const columns: TableProps<Subscription>["columns"] = [
    { title: "ID", dataIndex: "id", width: 64 },
    {
      title: "会话",
      dataIndex: "session",
      render: (value: string) => (
        <Typography.Text code copyable>
          {value}
        </Typography.Text>
      ),
    },
    { title: "备注", dataIndex: "note", render: (value: string) => value || "-" },
    {
      title: "启用",
      dataIndex: "enabled",
      width: 90,
      render: (_: boolean, record: Subscription) => (
        <Switch
          checked={record.enabled}
          loading={togglingId === record.id}
          onChange={(checked) => void toggle(record, checked)}
        />
      ),
    },
    {
      title: "创建时间",
      dataIndex: "created_at",
      width: 180,
      render: (value: string) => formatTime(value),
    },
    {
      title: "操作",
      width: 140,
      render: (_: unknown, record: Subscription) => (
        <Space>
          <Button type="link" onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="删除这条订阅？" onConfirm={() => void remove(record.id)}>
            <Button type="link" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Card
        title="订阅管理"
        extra={
          <Space>
            <Button onClick={() => void fillNotes()} loading={filling}>
              拉取群备注
            </Button>
            <Button type="primary" onClick={openCreate}>
              新增订阅
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          columns={columns}
          dataSource={items}
          loading={loading}
          pagination={false}
          scroll={{ x: 900 }}
        />
      </Card>
      <Modal
        title={editing ? "编辑订阅" : "新增订阅"}
        open={modalOpen}
        onOk={() => void submit()}
        confirmLoading={saving}
        onCancel={() => setModalOpen(false)}
      >
        {!editing && (
          <Space style={{ marginBottom: 16 }} wrap>
            <Button onClick={() => void loadGroups()} loading={groupLoading}>
              从群列表选择
            </Button>
            {groups.length > 0 && (
              <Select
                showSearch
                optionFilterProp="label"
                placeholder="选择群自动填充"
                style={{ minWidth: 260 }}
                options={groups.map((group) => ({
                  value: group.group_id,
                  label: `${group.group_name}（${group.group_id}）`,
                }))}
                onChange={(value: string) => {
                  const group = groups.find((item) => item.group_id === value);
                  if (group) {
                    form.setFieldsValue({
                      session: `aiocqhttp:GroupMessage:${group.group_id}`,
                      note: group.group_name,
                    });
                  }
                }}
              />
            )}
          </Space>
        )}
        <Form form={form} layout="vertical">
          <Form.Item
            name="session"
            label="会话标识"
            rules={[{ required: true, message: "填会话标识" }]}
            extra="平台:消息类型:会话ID，例如 aiocqhttp:GroupMessage:123"
          >
            <Input disabled={Boolean(editing)} />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input />
          </Form.Item>
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
