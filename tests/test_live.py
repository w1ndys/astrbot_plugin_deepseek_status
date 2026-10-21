# 真实网络冒烟：默认 skip，设置 DEEPSEEK_STATUS_LIVE=1 才请求状态页。
# 只验证公开接口的形状，不写库、不推送。
import os
import unittest

from astrbot_plugin_deepseek_status.business.collector import CollectorError, fetch_summary_active
from astrbot_plugin_deepseek_status.business.parser_api import parse_snapshot
from astrbot_plugin_deepseek_status.data.db import utc_now


@unittest.skipUnless(
    os.getenv("DEEPSEEK_STATUS_LIVE") == "1",
    "真实网络冒烟默认跳过；设 DEEPSEEK_STATUS_LIVE=1 开启",
)
class LiveStatusPageTest(unittest.IsolatedAsyncioTestCase):
    """请求真实 summary/active 并按真实结构解析。"""

    async def test_summary_active_shape(self):
        """能取到 data，active_changes 是数组，解析结果状态合法。"""
        try:
            data = await fetch_summary_active()
        except CollectorError as exc:
            self.fail(f"真实请求失败：{exc}")
        self.assertIn("active_changes", data)
        self.assertIsInstance(data["active_changes"], list)
        snapshot = parse_snapshot(data, utc_now())
        self.assertIn(snapshot.status, {"normal", "abnormal"})
        for event in snapshot.events:
            self.assertIsInstance(event.change_id, int)
            self.assertTrue(event.status)
            self.assertTrue(event.link.startswith("https://status.deepseek.com/"))


if __name__ == "__main__":
    unittest.main()
