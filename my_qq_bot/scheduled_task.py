"""
定时任务模块 - 处理定时发送消息的功能
"""

import os
import yaml
import asyncio
import time

from astrbot.api import logger
from astrbot.api.event import MessageChain
from astrbot.api.message_components import Image, Plain
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


class ScheduledTaskModule:
    """定时任务功能模块"""

    def __init__(self, context, source_dir):
        self.context = context
        self.source_dir = source_dir
        self.schedules = []
        self.scheduler = None

        # 加载定时任务配置
        self.load_scheduled_tasks()

        # 启动定时任务线程
        self.start_scheduler()

    def load_scheduled_tasks(self):
        """加载定时任务配置"""
        # 构建定时任务配置文件路径
        yaml_path = os.path.join(self.source_dir, "data", "scheduled.yaml")
        directory = os.path.dirname(yaml_path)

        # 若目录不存在则创建
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 若 YAML 文件不存在，创建一个空的定时任务配置
        if not os.path.exists(yaml_path):
            default_schedules = {"schedules": []}
            with open(yaml_path, "w", encoding="utf-8") as f:
                yaml.dump(default_schedules, f, allow_unicode=True, indent=2)

        # 从 YAML 文件加载定时任务
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.schedules = data.get("schedules", [])

    def start_scheduler(self):
        """启动定时任务调度器"""
        # 停止并清除现有的调度器
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()

        # 创建新的调度器
        self.scheduler = BackgroundScheduler()

        # 注册所有定时任务
        for scheduled_item in self.schedules:
            cron_expression = scheduled_item.get("schedule")
            tasks = scheduled_item.get("tasks", [])

            # 为每个任务创建一个调度
            for task in tasks:
                target = task.get("target")
                send_items = task.get("send", [])

                try:
                    # 使用 CronTrigger 直接支持 crontab 语法
                    self.scheduler.add_job(
                        self.run_scheduled_task,
                        CronTrigger.from_crontab(cron_expression),
                        args=[target, send_items],
                        id=f"task_{target}_{cron_expression.replace(' ', '_')}",
                    )

                    logger.info(f"已添加定时任务: {cron_expression} -> {target}")
                except Exception as e:
                    logger.error(f"添加定时任务失败: {cron_expression}, 错误: {str(e)}")

        # 启动调度器
        self.scheduler.start()

    def run_scheduled_task(self, target, send_items):
        """执行定时任务"""
        # 创建一个新的事件循环来运行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # 运行发送消息的异步任务
            loop.run_until_complete(self.send_scheduled_message(target, send_items))
        finally:
            loop.close()

    async def send_scheduled_message(self, target, send_items):
        """发送定时消息"""
        for item in send_items:
            reply_chain = []

            # 添加文本
            if item.get("text"):
                reply_chain.append(Plain(text=item["text"]))

            # 添加图片
            if item.get("images"):
                for image_url in item["images"]:
                    if image_url.startswith(("http://", "https://")):
                        reply_chain.append(Image.fromURL(url=image_url))
                    else:
                        reply_chain.append(Image.fromLocal(path=image_url))

            # 发送消息
            if reply_chain:
                chain = MessageChain()
                chain.chain.extend(reply_chain)
                try:
                    # 使用 API 发送消息到指定目标
                    await self.context.send_message(target, chain)
                    logger.info(f"已发送定时消息到 {target}")
                except Exception as e:
                    logger.error(f"发送定时消息失败: {str(e)}")
