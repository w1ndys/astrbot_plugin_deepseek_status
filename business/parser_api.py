# 业务层解析：把 summary/active 的原始数据归一化成 Snapshot 与 StatusEvent。
# 本文件不访问数据库，也不发请求；字段不合规时抛 ValueError，由 monitor 记日志。
from ..entity.constants import (
    CLOSED_EVENT_STATUSES,
    STATUS_ABNORMAL,
    STATUS_NORMAL,
    STATUS_PAGE_BASE,
)
from ..entity.models import Snapshot, StatusEvent


def event_link(change_id: int) -> str:
    """拼事件详情页地址；故障与计划维护都放在 incidents 路径下。"""
    return f"{STATUS_PAGE_BASE}/incidents/{change_id}"


def parse_event(item: dict) -> StatusEvent:
    """解析一条状态事件（含已结束的）；ID 必须是整数、状态必须是非空字符串。"""
    change_id = item.get("change_id")
    # 文档写 ID 是数字；字符串 "123" 不猜着转换，直接按结构异常处理
    if not isinstance(change_id, int):
        raise ValueError(f"active_changes[].change_id 必须是整数，收到 {type(change_id).__name__}")
    status = item.get("status")
    # 状态为空就判断不了事件是否结束，只能按结构异常处理
    if not isinstance(status, str) or not status:
        raise ValueError(f"active_changes[].status 必须是非空字符串，收到 {type(status).__name__}")
    # 标题与类型只用于展示；缺失或类型不对时收成空串，让文案层决定怎么写
    title = item.get("title")
    if not isinstance(title, str):
        title = ""
    change_type = item.get("type")
    if not isinstance(change_type, str):
        change_type = ""
    return StatusEvent(
        change_id=change_id,
        change_type=change_type,
        title=title,
        status=status,
        link=event_link(change_id),
    )


def parse_snapshot(data: dict, fetched_at: str) -> Snapshot:
    """把 summary/active 的 data 解析成快照；active_changes 必须是数组。"""
    active_changes = data.get("active_changes")
    # 缺字段或不是数组说明接口形状变了，抛 ValueError 让 monitor 记结构异常
    if not isinstance(active_changes, list):
        raise ValueError("active_changes 必须是数组")
    events: list[StatusEvent] = []
    for index, item in enumerate(active_changes):
        # 元素不是对象时带上下标，日志里能直接定位是第几条
        if not isinstance(item, dict):
            raise ValueError(f"active_changes[{index}] 必须是对象")
        events.append(parse_event(item))
    has_unfinished = False
    for event in events:
        # 只有未结束事件才算非正常；已结束的留在快照里，供下一轮比对状态变化
        if event.status not in CLOSED_EVENT_STATUSES:
            has_unfinished = True
            break
    status = STATUS_ABNORMAL if has_unfinished else STATUS_NORMAL
    return Snapshot(status=status, events=events, fetched_at=fetched_at)
