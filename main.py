import os
import sys
import json

# 导入AstrBot框架相关API
from astrbot.api import llm_tool  # 导入大语言模型工具
from astrbot.api.event import AstrMessageEvent  # 导入消息事件相关类
from astrbot.api.all import event_message_type, EventMessageType  # 导入事件类型和过滤器
from astrbot.api.star import Context, Star, register  # 导入插件注册和上下文管理相关类

# 获取当前脚本所在目录的绝对路径
source_dir = os.path.abspath(os.path.dirname(__file__))
# 将当前目录添加到Python模块搜索路径，确保可以导入自定义模块
sys.path.insert(0, source_dir)

# 导入自定义功能模块
from my_qq_bot import DoudouImageModule, KeywordReplyModule, ScheduledTaskModule


# 使用register装饰器注册插件，提供插件ID、作者、描述和版本信息
@register("my-qq-bot", "haowen-xu", "我的 qq 机器人", "1.0.0")
class MyQQBotPlugin(Star):
    """
    QQ机器人插件主类，继承自Star基类
    负责整合各个功能模块并处理消息事件
    """
    def __init__(self, context: Context):
        """
        初始化插件实例
        
        参数:
            context: 插件上下文对象，提供与AstrBot框架交互的接口
        """
        super().__init__(context)  # 调用父类初始化方法

        # 初始化豆豆照片模块 - 用于处理与猫咪照片相关的请求
        self.doudou_module = DoudouImageModule(context)

        # 初始化关键词回复模块 - 用于处理特定关键词的自动回复
        self.keyword_module = KeywordReplyModule(context, source_dir)

        # 初始化定时任务模块 - 用于处理定时执行的任务
        self.scheduled_module = ScheduledTaskModule(context, source_dir)

    # 使用装饰器注册消息处理函数，处理所有类型的消息事件
    @event_message_type(EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        """
        处理接收到的消息事件
        
        使用大语言模型(LLM)判断消息类型，根据类型调用相应的处理模块
        如果消息不符合预定义类型，则使用LLM生成自由回复
        
        参数:
            event: 消息事件对象，包含消息内容、发送者信息等
            
        返回:
            异步生成器，产生消息处理结果
        """
        # 获取用户发送的原始消息文本
        message_str = event.message_str
        
        # 获取LLM工具管理器，用于后续可能的LLM工具调用
        func_tools_mgr = self.context.get_llm_tool_manager()
        
        # 获取当前会话ID及上下文历史记录，用于维持对话连贯性
        curr_cid = await self.context.conversation_manager.get_curr_conversation_id(event.unified_msg_origin)
        conversation = None  # 会话对象
        context = []  # 会话历史上下文
        if curr_cid:
            # 如果存在当前会话ID，获取会话对象
            conversation = await self.context.conversation_manager.get_conversation(event.unified_msg_origin, curr_cid)
            # 从会话对象中解析历史记录，如果不存在则使用空列表
            context = json.loads(conversation.history) if conversation and conversation.history else []
        
        # 构建系统提示，指导LLM如何分类用户消息
        system_prompt = """
        你是一个消息分类助手，需要判断用户消息是否符合以下预定义类型之一：
        1. "豆豆照片请求" - 用户想看豆豆(一只猫)的照片
        2. "小豆照片请求" - 用户想看小豆(一只猫)的照片
        3. "问候" - 消息中包含"早安"或"晚安"等问候语
        4. "其他" - 不符合以上任何类型
        
        必须严格按照以下JSON格式返回，不要添加其他内容：
        {"分类":"类型名称","理由":"简短理由"}
        """
        
        # 调用LLM服务进行消息类型判断
        # 这里使用text_chat方法向LLM发送请求，不保存会话历史(session_id=None)
        llm_response = await self.context.get_using_provider().text_chat(
            prompt=message_str,  # 用户消息作为提示
            session_id=None,  # 不使用持久会话ID，这是一次性分类请求
            contexts=[{"role": "system", "content": system_prompt}],  # 设置系统提示作为上下文
            image_urls=event.get_image_urls() if hasattr(event, "get_image_urls") else [],  # 如果消息包含图片，传递图片URL
            func_tool=None,  # 不使用函数工具
            system_prompt=system_prompt  # 设置系统提示
        )
        print(llm_response)  # 打印完整的LLM响应，用于调试
        
        # 初始化消息类型判断结果变量
        message_type = "其他"  # 默认分类为"其他"
        reason = ""  # 分类理由
        
        # 检查LLM判断结果是否有效
        if llm_response.role == "assistant":  # 确认响应来自助手角色
            try:
                # 获取LLM回复的文本内容
                response_text = llm_response.completion_text
                
                # 输出LLM判断结果供调试
                print(f"LLM判断结果: {response_text}")
                
                # 尝试解析JSON格式的分类结果
                try:
                    # 提取JSON部分（如果回复中混合了其他内容）
                    json_start = response_text.find("{")  # 查找JSON开始位置
                    json_end = response_text.rfind("}") + 1  # 查找JSON结束位置
                    if json_start >= 0 and json_end > json_start:
                        # 提取JSON文本并解析
                        json_text = response_text[json_start:json_end]
                        result = json.loads(json_text)
                        # 从解析结果中获取分类和理由，如果不存在则使用默认值
                        message_type = result.get("分类", "其他")
                        reason = result.get("理由", "")
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试直接从文本中提取分类信息
                    # 这是一个后备方案，防止LLM没有严格按照JSON格式返回
                    if "豆豆照片请求" in response_text:
                        message_type = "豆豆照片请求"
                    elif "小豆照片请求" in response_text:
                        message_type = "小豆照片请求"
                    elif "问候" in response_text:
                        message_type = "问候"
                
                # 输出最终分类结果，用于调试
                print(f"分类结果: {message_type}, 理由: {reason}")
                
                # 根据分类结果调用相应的处理模块
                if message_type == "豆豆照片请求":
                    # 先向用户发送反馈，确认已识别请求类型
                    yield event.plain_result(f"检测到您想看豆豆的照片，马上为您安排~")
                    
                    # 使用通用的get_image方法处理豆豆照片请求，传递"豆豆"类别
                    async for result in self.doudou_module.get_image(event, "豆豆"):
                        yield result
                    return  # 处理完成后返回，不执行后续代码
                
                elif message_type == "小豆照片请求":
                    # 先向用户发送反馈，确认已识别请求类型
                    yield event.plain_result(f"检测到您想看小豆的照片，马上为您安排~")
                    
                    # 使用通用的get_image方法处理小豆照片请求，传递"小豆"类别
                    async for result in self.doudou_module.get_image(event, "小豆"):
                        yield result
                    return  # 处理完成后返回，不执行后续代码
                
                elif message_type == "问候":
                    # 根据具体问候类型向用户发送相应反馈
                    if "早安" in message_str:
                        yield event.plain_result("检测到早安问候，早安呀~")
                    elif "晚安" in message_str:
                        yield event.plain_result("检测到晚安问候，晚安啦~")
                    
                    # 使用关键词回复模块处理问候，并将结果传递给用户
                    async for result in self.keyword_module.handle_keyword_reply(event):
                        yield result
                    return  # 处理完成后返回，不执行后续代码
            
            except Exception as e:
                # 捕获并打印处理过程中的任何异常
                print(f"处理LLM判断结果时出错: {e}")
        
        # 如果没有匹配到预定义类型或处理过程出错，使用LLM生成自由回复
        # 这是一个兜底方案，确保用户总能得到回复
        yield event.request_llm(
            prompt=message_str,  # 用户原始消息作为提示
            func_tool_manager=func_tools_mgr,  # 传递LLM工具管理器
            session_id=curr_cid,  # 使用当前会话ID保持对话连贯性
            contexts=context,  # 传递历史上下文
            system_prompt="",  # 不使用特定系统提示
            image_urls=event.get_image_urls() if hasattr(event, "get_image_urls") else [],  # 如果消息包含图片，传递图片URL
            conversation=conversation  # 传递会话对象
        )
