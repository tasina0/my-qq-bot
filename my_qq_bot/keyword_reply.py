"""
关键词回复模块 - 处理关键词触发的自动回复功能
"""

import os
import random
import yaml

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.all import event_message_type, EventMessageType
from astrbot.api.message_components import Image, Plain


class KeywordReplyModule:
    """关键词回复功能模块"""

    def __init__(self, context, source_dir):
        self.context = context
        self.source_dir = source_dir
        self.triggers = []
        # 加载关键词回复配置
        self.load_keyword_reply_config()

    def load_keyword_reply_config(self):
        """加载关键词回复配置"""
        # 构建存储问答对的 YAML 文件路径
        yaml_path = os.path.join(self.source_dir, "data", "keyreply.yaml")
        directory = os.path.dirname(yaml_path)

        # 若目录不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 若 YAML 文件不存在，创建一个空的问答对配置
        if not os.path.exists(yaml_path):
            default_triggers = {"triggers": []}
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(default_triggers, f, allow_unicode=True, indent=2)

        # 从 YAML 文件加载问答对
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.triggers = data.get("triggers", [])

    @event_message_type(EventMessageType.ALL)
    async def handle_keyword_reply(self, event: AstrMessageEvent):
        """处理关键词回复功能"""
        message_str = event.message_str
        logger.info(f"收到消息: {event.unified_msg_origin}: {message_str[:100]}")

        # 遍历所有触发器进行匹配和回复
        for trigger in self.triggers:
            keyword = trigger["keyword"]
            answers = trigger["answers"]

            # 如果消息包含关键词则随机选择一个回答进行回复
            if keyword in message_str:
                # 随机选择一个回答
                answer = random.choice(answers)

                reply_chain = []
                if answer.get("text"):
                    reply_chain.append(Plain(text=answer["text"]))
                if answer.get("images"):
                    for image_url in answer["images"]:
                        if image_url.startswith(("http://", "https://")):
                            reply_chain.append(Image.fromURL(url=image_url))
                        else:
                            reply_chain.append(Image.fromLocal(path=image_url))
                yield event.chain_result(reply_chain)
