"""
Tag assignment for sentence patterns.

Uses keyword-based matching to categorise patterns into domains,
sentiment registers, and style buckets.
"""
from typing import Dict, List, Set, Tuple

# ── Keyword dictionaries ──────────────────────────────────────────────────────
#
# Structure: {tag_name: (category, [keywords])}
# 'category' is one of: domain | sentiment | style

TAG_DEFINITIONS: Dict[str, Tuple[str, List[str]]] = {
    # ── Domain ────────────────────────────────────────────────────────────────
    "政治": (
        "domain",
        ["建政", "制度", "执政", "执法", "政策", "国家", "政府", "党"],
    ),
    "手游": (
        "domain",
        ["游戏", "手游", "王者", "原神", "氪金", "充值", "技能", "段位", "上分", "开黑"],
    ),
    "饭圈": (
        "domain",
        ["爱豆", "粉丝", "应援", "出道", "打榜", "脱饭", "控评", "idol", "idol粉"],
    ),
    "职场": (
        "domain",
        ["打工", "上班", "老板", "摸鱼", "内卷", "卷", "年终奖", "职场", "绩效", "裁员"],
    ),
    "学业": (
        "domain",
        ["考试", "作业", "高考", "大学", "学习", "期末", "挂科", "成绩", "老师"],
    ),
    "情感": (
        "domain",
        ["恋爱", "表白", "分手", "喜欢", "爱情", "男朋友", "女朋友", "暗恋", "失恋"],
    ),
    "美食": (
        "domain",
        ["吃", "美食", "菜", "饭", "餐厅", "外卖", "奶茶", "火锅", "烧烤"],
    ),
    "科技": (
        "domain",
        ["AI", "人工智能", "ChatGPT", "程序", "代码", "算法", "互联网", "科技"],
    ),
    "体育": (
        "domain",
        ["球", "比赛", "运动员", "冠军", "训练", "足球", "篮球", "奥运"],
    ),
    "娱乐": (
        "domain",
        ["综艺", "剧", "明星", "电影", "音乐", "演唱会", "B站", "bilibili", "up主"],
    ),
    # ── Sentiment ─────────────────────────────────────────────────────────────
    "阴阳怪气": (
        "sentiment",
        ["阴阳", "讽刺", "挖苦", "嘲讽", "反话", "哦对", "真的假的", "哈哈哈哈", "好家伙"],
    ),
    "正能量": (
        "sentiment",
        ["加油", "努力", "坚持", "梦想", "奋斗", "相信", "感恩", "乐观"],
    ),
    "怨气": (
        "sentiment",
        ["烦", "气死", "无语", "讨厌", "恶心", "sb", "蠢", "崩溃", "绝望"],
    ),
    "感叹": (
        "sentiment",
        ["太", "真的", "居然", "竟然", "没想到", "天哪", "卧槽", "草", "这也行"],
    ),
    "无奈": (
        "sentiment",
        ["没办法", "算了", "随便", "无所谓", "躺平", "摆烂", "就这样吧"],
    ),
    # ── Style ─────────────────────────────────────────────────────────────────
    "网络用语": (
        "style",
        ["yyds", "绝绝子", "芭比Q", "破防", "泪目", "上头", "爷青回", "kkkk", "awsl", "xswl"],
    ),
    "成语化": (
        "style",
        ["之道", "之法", "之术", "主义", "有余", "不足", "无以"],
    ),
    "排比句": (
        "style",
        ["一是", "二是", "三是", "首先", "其次", "最后", "第一", "第二"],
    ),
    "反问句": (
        "style",
        ["难道", "不是吗", "不对吗", "凭什么", "为什么不", "何必"],
    ),
    "假设句": (
        "style",
        ["如果", "要是", "假如", "倘若", "万一", "假设"],
    ),
    "让步句": (
        "style",
        ["哪怕", "即使", "就算", "纵然", "尽管"],
    ),
}


def assign_tags(template_text: str, example_content: str = "") -> List[str]:
    """
    Return a list of tag names that match the given pattern template and/or example.

    Args:
        template_text: The pattern template string (with {slot} placeholders).
        example_content: An optional example sentence for additional signal.

    Returns:
        List of matching tag names (may be empty).
    """
    combined = (template_text + " " + example_content).lower()
    matched: List[str] = []

    for tag_name, (category, keywords) in TAG_DEFINITIONS.items():
        for kw in keywords:
            if kw.lower() in combined:
                matched.append(tag_name)
                break  # one hit is enough per tag

    return matched


def get_tag_category(tag_name: str) -> str:
    """Return the category for a known tag name, or 'style' as fallback."""
    entry = TAG_DEFINITIONS.get(tag_name)
    if entry:
        return entry[0]
    return "style"
