import os
import random

import yaml

from astrbot.api import llm_tool
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.all import event_message_type, EventMessageType
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star, register

source_dir = os.path.abspath(os.path.dirname(__file__))


@register("my-qq-bot", "haowen-xu", "我的 qq 机器人", "1.0.0")
class MyQQBotPlugin(Star):

    def __init__(self, context: Context):
        super().__init__(context)

        # 加载关键词回复配置
        self.load_keyword_reply_config()

    # =======
    # 豆豆照片
    # =======

    @llm_tool(name="get_doudou_image")
    async def get_doudou_image(self, event: AstrMessageEvent) -> MessageEventResult:
        """返回一张豆豆的照片。
        """
        # 随机决定是发送图片还是文字
        if random.random() < 0.8:
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
        else:
            # 随机回复的文字列表
            responses = [
                "豆豆真可爱~",
                "想看豆豆吗?",
                "不给看"
            ]
            yield event.plain_result(random.choice(responses))

    # =========
    # 关键词回复
    # =========
    def load_keyword_reply_config(self):
        """加载关键词回复配置"""
        # 构建存储问答对的 YAML 文件路径
        yaml_path = os.path.join(source_dir, 'data', 'keyreply.yaml')
        directory = os.path.dirname(yaml_path)

        # 若目录不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 若 YAML 文件不存在，创建一个空的问答对配置
        if not os.path.exists(yaml_path):
            default_triggers = {"triggers": []}
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_triggers, f, allow_unicode=True, indent=2)

        # 从 YAML 文件加载问答对
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            self.triggers = data.get('triggers', [])

    @event_message_type(EventMessageType.ALL)
    async def handle_keyword_reply(self, event: AstrMessageEvent):
        """处理关键词回复功能"""
        message_str = event.message_str

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
                        if image_url.startswith(('http://', 'https://')):
                            reply_chain.append(Image.fromURL(url=image_url))
                        else:
                            reply_chain.append(Image.fromLocal(path=image_url))
                yield event.chain_result(reply_chain)
