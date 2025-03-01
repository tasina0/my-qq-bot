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

    # =======
    # 当前时间
    # =======
    @llm_tool(name="get_current_time")  # 如果 name 不填，将使用函数名
    async def get_current_time(self, event: AstrMessageEvent) -> MessageEventResult:
        """获取当前时间。"""
        now = datetime.now()
        current_time = now.strftime("%Y年%m月%d日 %H点%M分%S秒")
        resp = f"现在的时间是 {current_time}。"
        yield event.plain_result(resp)

    # =======
    # 随机图片
    # =======
    @llm_tool(name="get_random_image")
    async def get_random_image(self, event: AstrMessageEvent, category: str = "老婆") -> MessageEventResult:
        """返回一张随机图片。

        Args:
            category(string): 图片分类，可选值为:

                - "老婆"
                - "豆豆"
        """
        # 检查分类是否正确
        if category not in ["老婆", "豆豆"]:
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
