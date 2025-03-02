"""
豆豆照片模块 - 处理返回豆豆照片的请求
"""

import os
import random

from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.message_components import Image


class DoudouImageModule:
    """豆豆照片功能模块"""

    def __init__(self, context):
        self.context = context
        # self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../images'))
        self.root_dir = r'C:\my robot\pictures'

    async def get_image(self, event: AstrMessageEvent, category: str) -> MessageEventResult:
        """返回指定类别的一张图片。"""
        # 验证 category 防止注入攻击
        if (not os.path.isdir(self.root_dir)) or (category not in os.path.listdir(self.root_dir)):
            yield event.plain_result(f"类别 '{category}' 不存在。")
            return

        # 构建类别目录路径
        category_dir = os.path.join(self.root_dir, category)

        # 验证类别目录是否存在
        if not os.path.isdir(category_dir):
            yield event.plain_result(f"类别 '{category}' 不存在。")
            return

        # 随机决定是发送图片还是文字
        if random.random() < 0.8:
            # 获取类别图片
            image_files = [
                f
                for f in os.listdir(category_dir)
                if f.lower().endswith((".jpg", ".png", ".gif", ".webp"))
            ]
            if not image_files:
                yield event.plain_result(f"没有找到任何 '{category}' 的图片。")
                return

            # 随机选择一张图片
            random_image = random.choice(image_files)
            image_path = os.path.join(category_dir, random_image)
            chain = [
                Image.fromFileSystem(image_path),
            ]
            yield event.chain_result(chain)
        else:
            # 随机回复的文字列表
            responses = [
                f"{category}真可爱~",
                f"想看{category}吗?",
                f"{category}不想出镜",
            ]
            yield event.plain_result(random.choice(responses))
