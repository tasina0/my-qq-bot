import os
import sys

from astrbot.api import llm_tool
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.all import event_message_type, EventMessageType
from astrbot.api.star import Context, Star, register

source_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, source_dir)

# 导入自定义模块
from my_qq_bot import DoudouImageModule, KeywordReplyModule, ScheduledTaskModule


@register("my-qq-bot", "haowen-xu", "我的 qq 机器人", "1.0.0")
class MyQQBotPlugin(Star):

    def __init__(self, context: Context):
        super().__init__(context)

        # 初始化豆豆照片模块
        self.doudou_module = DoudouImageModule(context)

        # 初始化关键词回复模块
        self.keyword_module = KeywordReplyModule(context, source_dir)

        # 初始化定时任务模块
        self.scheduled_module = ScheduledTaskModule(context, source_dir)

    # =======
    # 豆豆照片
    # =======
    @llm_tool(name="get_doudou_image")
    async def get_doudou_image(self, event: AstrMessageEvent) -> MessageEventResult:
        """返回一张豆豆的照片。"""
        async for result in self.doudou_module.get_doudou_image(event):
            yield result

    # =========
    # 关键词回复
    # =========
    @event_message_type(EventMessageType.ALL)
    async def handle_keyword_reply(self, event: AstrMessageEvent):
        """处理关键词回复功能"""
        async for result in self.keyword_module.handle_keyword_reply(event):
            yield result
