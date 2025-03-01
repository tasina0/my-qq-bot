import os
import random
from datetime import datetime

from astrbot.api import llm_tool
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star, register
from astrbot.core.message.message_event_result import MessageEventResult


@register("my-qq-bot", "haowen-xu", "我的 qq 机器人", "1.0.0")
class MyQQBotPlugin(Star):

    def __init__(self, context: Context):
        super().__init__(context)

    @llm_tool(name="get_doudou_image")
    async def get_doudou_image(self, event: AstrMessageEvent) -> MessageEventResult:
        """返回一张豆豆的照片。
        """
        # 获取图片文件夹路径
        image_folder = f"C:\\my robot\\pictures\\豆豆" 
        image_files = [
            f for f in os.listdir(image_folder)
            if f.lower().endswith((".jpg", ".png", ".gif", ".webp"))
        ]
        if not image_files:
            yield event.plain_result("没有找到任何图片。")
            return

        # 随机选择一张图片
        random_image = random.choice(image_files)
        image_path = os.path.join(image_folder, random_image)
        chain = [
            Image.fromFileSystem(image_path),
        ]
        yield event.chain_result(chain)

    @llm_tool(name="genshin_quote")
    async def genshin_quote(self, event: AstrMessageEvent) -> MessageEventResult:
        """返回一句原神相关的话。
        
        如果对方说了有关原神的话，AI 可以从中选取一句回复。
        """
        quotes = [
            "「旅行者，你今天也要继续冒险吗？」",
            "「风带来故事的种子，时间使之发芽。」", 
            "「星星总在夜空闪耀，就像你的眼睛。」",
            "「愿风神护佑你。」",
            "「璃月的夜市可是出了名的热闹。」",
            "「稻妻的樱花开得真美啊。」",
            "「须弥的智慧之神在指引着我们。」",
            "「枫丹的科技真是令人惊叹。」",
            "「纳塔的沙漠中藏着无数秘密。」",
            "「提瓦特大陆的每个角落都值得探索。」",
            "「荧，我们一起去冒险吧！」",
            "「派蒙永远是你最好的伙伴！」",
            "「今天也是美好的冒险日和呢。」",
            "「听说璃月港的海鲜很新鲜。」",
            "「蒙德城的自由之风吹拂着大地。」"
        ]
        quote = random.choice(quotes)
        yield event.plain_result(quote)
