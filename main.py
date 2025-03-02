import os
import sys
import json

from astrbot.api import llm_tool
from astrbot.api.event import AstrMessageEvent, MessageEventResult
from astrbot.api.all import event_message_type, EventMessageType, filter
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

    # 智能消息处理函数
    @event_message_type(EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        """
        处理消息，使用LLM判断是否符合预定义情况，如果符合则调用相应模块处理，
        否则使用LLM生成回复
        """
        # 获取用户消息
        message_str = event.message_str
        
        # 获取LLM工具管理器
        func_tools_mgr = self.context.get_llm_tool_manager()
        
        # 获取当前会话ID及上下文
        curr_cid = await self.context.conversation_manager.get_curr_conversation_id(event.unified_msg_origin)
        conversation = None
        context = []
        if curr_cid:
            conversation = await self.context.conversation_manager.get_conversation(event.unified_msg_origin, curr_cid)
            context = json.loads(conversation.history) if conversation and conversation.history else []
        
        # 构建系统提示，用于LLM判断消息类型
        system_prompt = """
        你是一个消息分类助手，需要判断用户消息是否符合以下预定义类型之一：
        1. "豆豆照片请求" - 用户想看豆豆(一只猫)的照片
        2. "小豆照片请求" - 用户想看小豆(一只猫)的照片
        3. "问候" - 消息中包含"早安"或"晚安"等问候语
        4. "其他" - 不符合以上任何类型
        
        必须严格按照以下JSON格式返回，不要添加其他内容：
        {"分类":"类型名称","理由":"简短理由"}
        """
        
        # 调用LLM进行消息类型判断
        llm_response = await self.context.get_using_provider().text_chat(
            prompt=message_str,
            session_id=None,
            contexts=[{"role": "system", "content": system_prompt}],
            image_urls=event.get_image_urls() if hasattr(event, "get_image_urls") else [],
            func_tool=None,
            system_prompt=system_prompt
        )
        print(llm_response)
        
        # 判断结果变量
        message_type = "其他"
        reason = ""
        
        # 检查LLM判断结果
        if llm_response.role == "assistant":
            try:
                # 获取LLM回复文本
                response_text = llm_response.completion_text
                
                # 输出LLM判断结果供调试
                print(f"LLM判断结果: {response_text}")
                
                # 尝试解析JSON
                try:
                    # 提取JSON部分（如果回复中混合了其他内容）
                    json_start = response_text.find("{")
                    json_end = response_text.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = response_text[json_start:json_end]
                        result = json.loads(json_text)
                        message_type = result.get("分类", "其他")
                        reason = result.get("理由", "")
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，尝试直接从文本中提取分类信息
                    if "豆豆照片请求" in response_text:
                        message_type = "豆豆照片请求"
                    elif "小豆照片请求" in response_text:
                        message_type = "小豆照片请求"
                    elif "问候" in response_text:
                        message_type = "问候"
                
                # 输出分类结果
                print(f"分类结果: {message_type}, 理由: {reason}")
                
                # 根据分类结果处理消息
                if message_type == "豆豆照片请求":
                    # 先向用户反馈被识别的请求类型
                    yield event.plain_result(f"检测到您想看豆豆的照片，马上为您安排~")
                    
                    # 处理豆豆照片请求
                    async for result in self.doudou_module.get_doudou_image(event):
                        yield result
                    return
                
                elif message_type == "小豆照片请求":
                    # 先向用户反馈被识别的请求类型
                    yield event.plain_result(f"检测到您想看小豆的照片，马上为您安排~")
                    
                    # 处理小豆照片请求
                    async for result in self.doudou_module.get_xiaodou_image(event):
                        yield result
                    return
                
                elif message_type == "问候":
                    # 向用户反馈
                    if "早安" in message_str:
                        yield event.plain_result("检测到早安问候，早安呀~")
                    elif "晚安" in message_str:
                        yield event.plain_result("检测到晚安问候，晚安啦~")
                    
                    # 使用关键词回复模块处理问候
                    async for result in self.keyword_module.handle_keyword_reply(event):
                        yield result
                    return
            
            except Exception as e:
                print(f"处理LLM判断结果时出错: {e}")
        
        # 如果没有匹配到预定义类型或处理出错，使用LLM生成自由回复
        yield event.request_llm(
            prompt=message_str,
            func_tool_manager=func_tools_mgr,
            session_id=curr_cid,
            contexts=context,
            system_prompt="",
            image_urls=event.get_image_urls() if hasattr(event, "get_image_urls") else [],
            conversation=conversation
        )
