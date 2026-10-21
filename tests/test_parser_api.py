# 解析层测试：事件链接、单条事件字段校验与整体快照归一化。
# 不联网、不导入 astrbot；正常态用落盘的实测 fixture，非正常态用构造对象。
import json
import unittest
from pathlib import Path

from astrbot_plugin_deepseek_status.business.parser_api import (
    event_link,
    parse_event,
    parse_snapshot,
)
from astrbot_plugin_deepseek_status.entity.constants import (
    STATUS_ABNORMAL,
    STATUS_NORMAL,
    STATUS_PAGE_BASE,
)

# 实测成功响应样本，正常态解析直接用它
FIXTURE = Path(__file__).parent / "fixtures" / "summary_active.json"


class EventLinkTest(unittest.TestCase):
    """事件链接由页面根地址与事件 ID 拼成。"""

    def test_link_uses_incidents_path(self):
        """详情页固定在 incidents 路径下，ID 原样出现在末尾。"""
        expected = f"{STATUS_PAGE_BASE}/incidents/6410630422455"
        self.assertEqual(event_link(6410630422455), expected)


class ParseEventTest(unittest.TestCase):
    """单条事件：必填字段校验，标题与类型缺失时兜底。"""

    def test_full_item_maps_every_field(self):
        """完整事件原样映射，链接由 ID 拼出。"""
        event = parse_event(
            {
                "change_id": 6410630422455,
                "type": "incident",
                "title": "API 延迟升高",
                "status": "investigating",
            }
        )
        self.assertEqual(event.change_id, 6410630422455)
        self.assertEqual(event.change_type, "incident")
        self.assertEqual(event.title, "API 延迟升高")
        self.assertEqual(event.status, "investigating")
        self.assertEqual(event.link, event_link(6410630422455))

    def test_change_id_must_be_int(self):
        """缺失、字符串或小数的 ID 都算结构异常，并指出字段名。"""
        for bad in (None, "123", 12.5):
            with self.subTest(change_id=bad):
                with self.assertRaises(ValueError) as caught:
                    parse_event({"change_id": bad, "status": "investigating"})
                self.assertIn("change_id", str(caught.exception))

    def test_status_must_be_non_empty_string(self):
        """状态缺失、空串或非字符串都算结构异常，并指出字段名。"""
        for bad in (None, "", 123):
            with self.subTest(status=bad):
                with self.assertRaises(ValueError) as caught:
                    parse_event({"change_id": 1, "status": bad})
                self.assertIn("status", str(caught.exception))

    def test_optional_fields_default_to_empty_string(self):
        """缺标题与类型时仍按正常事件收下，两个字段变成空串。"""
        event = parse_event({"change_id": 1, "status": "investigating"})
        self.assertEqual(event.title, "")
        self.assertEqual(event.change_type, "")


class ParseSnapshotTest(unittest.TestCase):
    """整体快照：保留全部事件，整体状态只看未结束事件。"""

    def make_change(self, change_id: int, status: str) -> dict:
        """构造一条最小事件；非空 active_changes 还没有实测样本，只能构造。"""
        return {
            "change_id": change_id,
            "type": "incident",
            "title": f"事件{change_id}",
            "status": status,
        }

    def test_fixture_normal_snapshot(self):
        """实测空 active_changes：整体正常，事件列表为空。"""
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))["data"]
        snapshot = parse_snapshot(data, "2026-10-20T00:00:00Z")
        self.assertEqual(snapshot.status, STATUS_NORMAL)
        self.assertEqual(snapshot.events, [])
        self.assertEqual(snapshot.fetched_at, "2026-10-20T00:00:00Z")

    def test_keeps_closed_events_but_status_counts_unfinished(self):
        """一条调查中 + 一条已解决：两条都保留，整体仍是非正常。"""
        changes = [self.make_change(1, "investigating"), self.make_change(2, "resolved")]
        snapshot = parse_snapshot({"active_changes": changes}, "2026-10-20T00:00:00Z")
        self.assertEqual(len(snapshot.events), 2)
        self.assertEqual(snapshot.status, STATUS_ABNORMAL)

    def test_only_closed_events_is_normal(self):
        """只剩已结束事件：整体正常，但事件仍留在快照里供下一轮比对。"""
        changes = [self.make_change(3, "completed")]
        snapshot = parse_snapshot({"active_changes": changes}, "2026-10-20T00:00:00Z")
        self.assertEqual(snapshot.status, STATUS_NORMAL)
        self.assertEqual(len(snapshot.events), 1)

    def test_active_changes_must_be_list(self):
        """缺 active_changes 或不是数组：结构异常，消息含字段名。"""
        for data in ({}, {"active_changes": "x"}, {"active_changes": None}):
            with self.subTest(data=data):
                with self.assertRaises(ValueError) as caught:
                    parse_snapshot(data, "2026-10-20T00:00:00Z")
                self.assertIn("active_changes", str(caught.exception))

    def test_element_must_be_object(self):
        """元素不是对象：结构异常，消息带下标方便定位。"""
        with self.assertRaises(ValueError) as caught:
            parse_snapshot({"active_changes": ["x"]}, "2026-10-20T00:00:00Z")
        self.assertIn("active_changes[0]", str(caught.exception))


# 允许直接 python3 tests/test_parser_api.py 运行本文件
if __name__ == "__main__":
    unittest.main()
