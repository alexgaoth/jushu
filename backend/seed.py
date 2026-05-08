"""
Seed the database with sample Chinese internet fixed expressions.
Run: python seed.py
"""
import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import RawText
from crawlers.base import sha256_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Sample sentences — mix of connective patterns, internet memes, and classic 神评
SEED_SENTENCES = [
    # 只有...才...
    "只有努力学习，才能考上好大学",
    "只有经历过痛苦，才能真正理解幸福",
    "只有你先爱自己，别人才会爱你",
    "只有真正的朋友，才会在你最难的时候出现",
    "只有失去过，才知道珍惜",
    # 虽然...但是...
    "虽然我很穷，但是我快乐",
    "虽然长得不好看，但是我有钱啊",
    "虽然努力不一定成功，但是不努力一定失败",
    "虽然结局很悲伤，但是过程很美好",
    "虽然前路漫漫，但是初心不变",
    # 宁可...也不...
    "宁可累死在路上，也不闲死在家里",
    "宁可站着死，也不跪着生",
    "宁可做过后悔，也不要不做遗憾",
    "宁可孤独也不将就",
    "宁可和聪明的人吵架，也不和傻瓜谈恋爱",
    # 不是...而是...
    "不是我不想努力，而是不知道努力的方向",
    "不是钱的问题，而是根本没有钱的问题",
    "不是不爱你，而是爱得太累了",
    "不是不想见你，而是见了更想你",
    "成功不是偶然的，而是必然的",
    # 既然...那就...
    "既然选择了远方，那就风雨兼程",
    "既然改变不了世界，那就改变自己",
    "既然无法回头，那就努力向前",
    "既然爱了，那就好好爱",
    "既然来了，那就把它做好",
    # 与其...不如...
    "与其等待机会，不如创造机会",
    "与其抱怨黑暗，不如点亮蜡烛",
    "与其纠结过去，不如把握现在",
    "与其羡慕别人，不如提升自己",
    "与其相见恨晚，不如就此别过",
    # 就算...也...
    "就算全世界都不理解你，我也会站在你这边",
    "就算输掉一切，也不能输掉自己",
    "就算生活再难，也要笑着过",
    "就算走得很慢，也不要停下来",
    "就算跌倒一百次，也要一百零一次站起来",
    # 如果...就...
    "如果你累了，就休息一下，不要放弃",
    "如果生活欺骗了你，就欺骗回去",
    "如果可以重来，我还是会选择你",
    "如果爱是一场梦，就让我永远不要醒来",
    # Chinese internet meme patterns
    "我太难了",
    "打工人，打工魂，打工都是人上人",
    "躺平就是我的养生之道",
    "内卷这么严重，不如直接摆烂",
    "yyds，永远的神",
    "这个真的绝了，狠狠拿捏了",
    "破防了，真的破防了",
    "家人们谁懂啊，我真的哭死",
    "整个人都不好了",
    "奥里给，干了兄弟们",
    "我裂开了",
    "给我整不会了",
    "有被笑到，笑不活了",
    "DNA动了",
    "我悟了",
    "栓Q",
    "太顶了这个",
    "绝绝子",
    "确实，但没必要",
    "这不是人干的事",
    "人在做，天在看",
    "做人留一线，日后好相见",
    "出来混，迟早要还的",
    "不是哥们，你这样做不对",
    "我哭了，真的哭了",
    # 阴阳怪气 patterns
    "好耶，又是元气满满的一天呢",
    "哇，真的好厉害，我学到了",
    "好的好的，您说得对",
    "感谢您的指正，我会努力改正的",
    "真的太感谢了，感动哭了",
    # 神评 classics
    "来都来了",
    "你行你上啊",
    "看看谁比你惨",
    "这不就是人生写照",
    "懂的都懂，说的就是你",
    "这波在第五层",
    "格局打开",
    "高手在民间",
    "话不多说，直接开冲",
    "低调低调，不要让他们看出来我很菜",
]


async def main() -> None:
    logger.info("Seeding database with %d sample sentences...", len(SEED_SENTENCES))

    inserted = 0
    skipped = 0

    for sentence in SEED_SENTENCES:
        content_hash = sha256_hash(sentence)
        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                select(RawText.id).where(RawText.content_hash == content_hash)
            )
            if existing.scalar_one_or_none() is not None:
                skipped += 1
                continue

            raw = RawText(
                platform="seed",
                content_type="comment",
                raw_content=sentence,
                content_hash=content_hash,
                source_url="https://www.bilibili.com",
                timestamp=datetime.now(timezone.utc),
                processed=False,
            )
            db.add(raw)
            await db.commit()
            inserted += 1

    logger.info("Seed complete: %d inserted, %d already existed.", inserted, skipped)
    logger.info("Now run: python -m nlp.run_pipeline")


if __name__ == "__main__":
    asyncio.run(main())
