# 时区解析、渲染与变化汇总单测：合法 IANA、空值、固定偏移写法的回退，本地时间格式与推送版式。
import unittest
from zoneinfo import ZoneInfo

from astrbot_plugin_deepseek_status.business.text import (
    render_changes,
    render_help,
    render_status_reply,
    render_summary,
    resolve_timezone,
    to_local,
)
from astrbot_plugin_deepseek_status.entity.constants import (
    DEFAULT_TIMEZONE,
    SUBCOMMAND_HELP,
    SUBCOMMAND_OFF,
    SUBCOMMAND_ON,
)
from astrbot_plugin_deepseek_status.entity.models import Snapshot, StatusEvent


def _event(change_id: int, title: str, change_type: str, status: str) -> StatusEvent:
    """构造一条事件，链接按 ID 拼，够文案层使用。"""
    return StatusEvent(
        change_id=change_id,
        change_type=change_type,
        title=title,
        status=status,
        link=f"https://status.deepseek.com/incidents/{change_id}",
    )


class ResolveTimezoneTest(unittest.TestCase):
    """配置值到时区对象的解析规则。"""

    def test_valid_iana_name(self):
        """合法 IANA 名称原样解析。"""
        self.assertEqual(resolve_timezone("Asia/Shanghai"), ZoneInfo("Asia/Shanghai"))

    def test_empty_uses_default(self):
        """空字符串回退默认时区。"""
        self.assertEqual(resolve_timezone("").key, DEFAULT_TIMEZONE.key)

    def test_fixed_offset_falls_back(self):
        """UTC+8 这类固定偏移不是 IANA 名称，回退默认。"""
        self.assertEqual(resolve_timezone("UTC+8").key, DEFAULT_TIMEZONE.key)

    def test_unknown_name_falls_back(self):
        """不存在的时区名回退默认。"""
        self.assertEqual(resolve_timezone("Mars/Olympus").key, DEFAULT_TIMEZONE.key)

    def test_utc_is_valid(self):
        """UTC 是合法名称，不触发回退。"""
        self.assertEqual(resolve_timezone("UTC").key, "UTC")


class ToLocalTest(unittest.TestCase):
    """UTC 采集时间到展示时区的格式。"""

    def test_shanghai(self):
        """UTC 12 点在东八区是 20 点，格式到秒。"""
        self.assertEqual(
            to_local("2026-10-20T12:00:00Z", ZoneInfo("Asia/Shanghai")),
            "2026-10-20 20:00:00",
        )

    def test_new_york_uses_dst(self):
        """纽约 10 月仍在夏令时，UTC 12 点是 08 点。"""
        self.assertEqual(
            to_local("2026-10-20T12:00:00Z", ZoneInfo("America/New_York")),
            "2026-10-20 08:00:00",
        )

    def test_crosses_date(self):
        """跨日时日期跟着时区变，不能只改小时。"""
        self.assertEqual(
            to_local("2026-10-20T23:30:00Z", ZoneInfo("Asia/Shanghai")),
            "2026-10-21 07:30:00",
        )

    def test_utc(self):
        """配置成 UTC 时原样输出，不加偏移后缀。"""
        self.assertEqual(to_local("2026-10-20T12:00:00Z", ZoneInfo("UTC")), "2026-10-20 12:00:00")


class RenderChangesTest(unittest.TestCase):
    """一轮多条变化的汇总版式。"""

    def test_two_changes(self):
        """多条变化按顺序编号，标题后跟类型/状态，链接缩进一行。"""
        changes = [
            _event(1, "网页/API 部分中断", "incident", "investigating"),
            _event(2, "计划维护：API 服务", "maintenance", "scheduled"),
        ]
        text = render_changes(changes, "2026-10-20T12:00:00Z", ZoneInfo("Asia/Shanghai"))
        self.assertEqual(
            text,
            "检测到 2 条变化（2026-10-20 20:00:00）\n"
            "1. 网页/API 部分中断（故障 / 调查中）\n"
            "   https://status.deepseek.com/incidents/1\n"
            "2. 计划维护：API 服务（计划维护 / 已排期）\n"
            "   https://status.deepseek.com/incidents/2",
        )

    def test_single_change(self):
        """一条变化也走同一版式，数量写 1。"""
        changes = [_event(9, "单条事件", "incident", "monitoring")]
        text = render_changes(changes, "2026-10-20T12:00:00Z", ZoneInfo("Asia/Shanghai"))
        self.assertTrue(text.startswith("检测到 1 条变化（"))

    def test_empty_title_uses_placeholder(self):
        """标题为空时用“未命名事件”占位。"""
        changes = [_event(3, "", "incident", "identified")]
        text = render_changes(changes, "2026-10-20T12:00:00Z", ZoneInfo("Asia/Shanghai"))
        self.assertIn("未命名事件", text)

    def test_unknown_type_and_status_kept_raw(self):
        """映射表里没有的类型/状态原样输出，不丢信息。"""
        changes = [_event(4, "未知事件", "other", "unknown_state")]
        text = render_changes(changes, "2026-10-20T12:00:00Z", ZoneInfo("Asia/Shanghai"))
        self.assertIn("（other / unknown_state）", text)


class RenderSummaryTest(unittest.TestCase):
    """订阅开启时的当前状态摘要。"""

    def test_normal_lists_no_events(self):
        """只有已结束事件时按正常处理，不列链接。"""
        snapshot = Snapshot(
            status="normal",
            events=[_event(1, "旧事件", "incident", "resolved")],
            fetched_at="2026-10-20T12:00:00Z",
        )
        text = render_summary(snapshot, ZoneInfo("Asia/Shanghai"))
        self.assertEqual(text, "当前状态：一切运行正常（2026-10-20 20:00:00）")

    def test_abnormal_lists_unfinished_only(self):
        """非正常时列出未结束事件，已结束的同轮事件不出现。"""
        snapshot = Snapshot(
            status="abnormal",
            events=[
                _event(1, "网页/API 部分中断", "incident", "investigating"),
                _event(2, "计划维护：API 服务", "maintenance", "scheduled"),
                _event(3, "旧事件", "incident", "resolved"),
            ],
            fetched_at="2026-10-20T12:00:00Z",
        )
        text = render_summary(snapshot, ZoneInfo("Asia/Shanghai"))
        self.assertEqual(
            text,
            "当前状态：有 2 条未结束事件（2026-10-20 20:00:00）\n"
            "1. 网页/API 部分中断（故障 / 调查中）\n"
            "   https://status.deepseek.com/incidents/1\n"
            "2. 计划维护：API 服务（计划维护 / 已排期）\n"
            "   https://status.deepseek.com/incidents/2",
        )
        self.assertNotIn("incidents/3", text)

    def test_empty_title_uses_placeholder(self):
        """未结束事件标题为空时同样用占位。"""
        snapshot = Snapshot(
            status="abnormal",
            events=[_event(5, "", "incident", "identified")],
            fetched_at="2026-10-20T12:00:00Z",
        )
        text = render_summary(snapshot, ZoneInfo("Asia/Shanghai"))
        self.assertIn("未命名事件", text)


class RenderStatusReplyTest(unittest.TestCase):
    """dsstatus 查状态的回复。"""

    def test_none_snapshot(self):
        """还没采到数据时提示刚启动。"""
        self.assertEqual(
            render_status_reply(None, ZoneInfo("Asia/Shanghai")),
            "监控刚启动，还没有数据",
        )

    def test_normal_reuses_summary(self):
        """有快照时与摘要正文一致。"""
        snapshot = Snapshot(
            status="normal",
            events=[],
            fetched_at="2026-10-20T12:00:00Z",
        )
        expected = render_summary(snapshot, ZoneInfo("Asia/Shanghai"))
        self.assertEqual(render_status_reply(snapshot, ZoneInfo("Asia/Shanghai")), expected)

    def test_abnormal_lists_events(self):
        """非正常时回复里带未结束事件与链接。"""
        snapshot = Snapshot(
            status="abnormal",
            events=[_event(1, "网页/API 部分中断", "incident", "investigating")],
            fetched_at="2026-10-20T12:00:00Z",
        )
        text = render_status_reply(snapshot, ZoneInfo("Asia/Shanghai"))
        self.assertIn("incidents/1", text)
        self.assertIn("调查中", text)


class RenderHelpTest(unittest.TestCase):
    """命令用法说明。"""

    def test_uses_given_command_name(self):
        """指令被改名后，帮助里用实际名字，不写死 dsstatus。"""
        text = render_help("dsmonitor")
        self.assertIn(f"dsmonitor {SUBCOMMAND_ON}", text)
        self.assertNotIn("dsstatus", text)

    def test_lists_status_and_switch_commands(self):
        """帮助里能看到查状态、开、关、帮助四条，子命令取自常量。"""
        text = render_help("dsstatus")
        for part in ("查看当前状态", SUBCOMMAND_ON, SUBCOMMAND_OFF, SUBCOMMAND_HELP):
            self.assertIn(part, text)


if __name__ == "__main__":
    unittest.main()
