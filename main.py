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

    @llm_tool(name="get_image")
    async def get_image(self, event: AstrMessageEvent, category: str) -> MessageEventResult:
        """返回一张图片。

        Args:
            category(string): 图片分类，可选值为:

                - "豆豆"
                - "小猫"
        """
        # 检查分类是否正确
        if category not in ["豆豆", "小猫"]:
            yield event.plain_result("没有找到任何图片。")
            return

        # 获取图片文件夹路径
        image_folder = f"C:\\my robot\\pictures\\{category}" 
        image_files = [f for f in os.listdir(image_folder) if f.endswith(".jpg")]
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
            "「枫丹的科技真是令人惊叹。」"
        ]
        quote = random.choice(quotes)
        yield event.plain_result(quote)
