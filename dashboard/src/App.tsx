// 三个 Tab 的容器；7.2–7.4 再把占位替换成真实视图。
import { ConfigProvider, Tabs } from "antd";
import type { TabsProps } from "antd";

import ChangesView from "./changes-view";
import StatusView from "./status-view";
import SubscriptionsView from "./subscriptions-view";

const items: TabsProps["items"] = [
  {
    key: "status",
    label: "概览与配置",
    children: <StatusView />,
  },
  {
    key: "subscriptions",
    label: "订阅管理",
    children: <SubscriptionsView />,
  },
  {
    key: "changes",
    label: "变更记录",
    children: <ChangesView />,
  },
];

export default function App() {
  return (
    <ConfigProvider>
      <Tabs className="page-tabs" defaultActiveKey="status" items={items} />
    </ConfigProvider>
  );
}
