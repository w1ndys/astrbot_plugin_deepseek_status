// 插件视图入口：单页挂载三个 Tab；bridge SDK 由 AstrBot Dashboard 提供。
// 按宿主 query 的 theme/isDark 先铺底色，避免 iframe 加载时白闪。
import { StyleProvider } from "@ant-design/cssinjs";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./style.css";

const params = new URLSearchParams(window.location.search);
const dark = params.get("isDark") === "1" || params.get("theme") === "dark";
document.documentElement.dataset.theme = dark ? "dark" : "light";

const container = document.getElementById("root");
if (!container) {
  throw new Error("缺少 #root 挂载点");
}

createRoot(container).render(
  <StrictMode>
    <StyleProvider layer>
      <App />
    </StyleProvider>
  </StrictMode>,
);
