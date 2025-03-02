"""
豆豆照片模块 - 处理返回豆豆照片的请求
"""

import os
import random

from astrbot.api import llm_tool, logger
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.message_components import Image, Plain


class DoudouImageModule:
    """豆豆照片功能模块"""

    def __init__(self, context):
        self.context = context
        # 图片文件夹路径
        self.image_folder = r"C:\my robot\pictures\豆豆"

    @llm_tool(name="get_doudou_image")
    async def get_doudou_image(self, event: AstrMessageEvent) -> MessageEventResult:
        """返回一张豆豆的照片。"""
        # 随机决定是发送图片还是文字
        if random.random() < 0.8:
            # 获取豆豆图片
            image_files = [
                f
                for f in os.listdir(self.image_folder)
                if f.lower().endswith((".jpg", ".png", ".gif", ".webp"))
            ]
            if not image_files:
                yield event.plain_result("没有找到任何图片。")
                return

            # 随机选择一张图片
            random_image = random.choice(image_files)
            image_path = os.path.join(self.image_folder, random_image)
            chain = [
                Image.fromFileSystem(image_path),
            ]
            yield event.chain_result(chain)
        else:
            # 随机回复的文字列表
            responses = ["豆豆真可爱~", "想看豆豆吗?", "不给看"]
            yield event.plain_result(random.choice(responses))
