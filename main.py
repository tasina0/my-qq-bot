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

    @llm_tool(name="get_character_picture")
    async def get_character_picture(self, event: AstrMessageEvent, category: str = "豆豆") -> MessageEventResult:
        """返回一张指定对象的图片。

        Args:
            category(string): 图片分类，可选值为:

                - "豆豆"
        """
        # 检查分类是否正确
        if category not in ["豆豆"]:
            yield event.plain_result("图片分类错误，请输入正确的分类。")
            return

        # 获取图片文件夹路径
        image_folder = f"D:\\projects\\my-qq-bot\\images\\{category}"
        image_files = [f for f in os.listdir(image_folder) if f.endswith(".jpg")]
        if not image_files:
            yield event.plain_result("没有找到任何图片。")
            return

        # 随机选择一张图片
        random_image = random.choice(image_files)
        image_path = os.path.join(image_folder, random_image)
        chain = [
            Plain("来看这个图："),
            Image.fromFileSystem(image_path),
            Plain("这是一个随机图片。"),
        ]
        yield event.chain_result(chain)
