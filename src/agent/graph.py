import asyncio
from typing import Annotated, Callable, Awaitable

from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse, ExtendedModelResponse
from langchain.agents.middleware.types import ResponseT
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.typing import ContextT

from agent.custom_llm import deepseek_chat_model
from agent.utils.log_util import log
from agent.utils.tools import load_skill
from agent.utils import python_tools

def get_tools_by_skill(skill_name: str, all_tools: dict[str, list[BaseTool]]) -> list[BaseTool]:
    """根据技能名称获取对应的工具列表"""
    skill_tool_mapping = {
        "python_execution": all_tools.get("python_execution", []),
        "basic_skill": all_tools.get("basic", []), # 每个技能对应的工具列表
    }
    return skill_tool_mapping.get(skill_name)

class SkillState(AgentState):
    """技能状态管理"""

    # 已加载的技能列表，lambda 表达式的含义：有两个列表 current 和 new，遍历 new 列表中的每一个元素，如果该元素不在 current 列表中，就把他加进去
    skills_loaded: Annotated[list[str], lambda current, new: current + [s for s in new if s not in current]]

class SkillMiddleware(AgentMiddleware):
    """
    加载技能中间件：实现渐进式工具加载，并对日志进行智能化管理

    核心功能：
    1. 状态感知：监控技能加载状态并相应调整行为
    2. 动态工具过滤：根据已加载的技能动态调用可用的工具列表
    3. 错误恢复：在异常情况下优雅的降级到基础工具集
    4. 智能日志：避免重复日志输出，提升调试效率

    设计原理：
    基于 Claude Skills 架构，通过中间件拦截模型调用，实现工具的动态加载和卸载，
    这种架构解决了传统 Agent 一次性暴露所有工具，进而导致“工具过多降智”问题
    """

    def __init__(self, all_tools: dict[str, list[BaseTool]]):
        """
        初始化技能中间件

        Args:
            all_tools: dict[str, list[BaseTool]] 按技能类别分类所有工具
            例如：{"system": [get_time, get_weather]}

        初始化过程：
            1. 调用父类初始化
            2. 存储工具分类字典
            3. 设置基础工具（始终可用的工具，如：load_skill）
            4. 预注册所有工具到中间件
            5. 初始化状态缓存机制
        """
        super().__init__() # 调用父类 AgentMiddleware 的初始化方法
        self.all_tools = all_tools # 按类别分类的所有工具
        self.base_tools = [load_skill] # 基础工具，始终对 Agent 可见

        # 预注册所有工具到中间件，确保系统能识别所有工具
        self._pre_register_all_tools()

        # 初始化状态缓存机制，用于优化性能和避免重复日志
        self.last_skills_loaded = set() # 上次已加载的技能集合（使用集合提高查询效率）
        self.logged_skill_tools = set() # 已记录过日志的技能工具集合（避免日志重复输出）

    def _pre_register_all_tools(self):
        """
        预先注册所有工具到中间件系统

        为什么要预注册：
        - 中间件机制要求所有可能使用到的工具必须在中间件中预注册，否则在动态添加工具时会报 “unknow tool names” 错误
        - 这确保了系统能够正确识别和验证所有工具名称

        实现步骤：
        1. 从分类工具字典中提取所有工具
        2. 合并基础工具和分类工具
        3. 将合并后的工具列表注册到中间件的 tools 属性
        """

        # 所有工具合计
        all_tools_instances = []
        for tool_category in self.all_tools.values():
            all_tools_instances.extend(tool_category)

        # 合并基础工具和分类工具，并注册到中间件的 tools 属性
        self.tools = self.base_tools + all_tools_instances

    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT] | AIMessage | ExtendedModelResponse[ResponseT]:
        """
        异步模型调用包装方法 - 中间的核心逻辑

        执行流程：
        1. 状态检查：检查已加载的技能状态
        2. 工具过滤：根据技能状态构建工具列表
        3. 提示更新：更新系统消息中的技能提示信息
        4. 请求修改：创建包含过滤后工具的新请求
        5. 调用处理：将修改后的请求传递给下一个处理器

        参数：
            request: ModelRequest[ContextT] - 包含当前模型调用请求的所有信息
                - messages: 消息历史
                - tools: 当前可用的工具列表
                - state: 当前 Agent 状态（包含 skills_loaded 等）
            handler: Callable - 下一个中间件或最终模型调用处理器

        返回：
            ModelResponse - 模型调用响应结果
        """

        try:
            # --- 1. 状态检测
            # 从请求状态中获取当前已加载的技能列表（转换为集合提高查询效率）
            current_skills = set(request.state.get('skills_loaded', []))

            # 使用集合运算检测出状态变化：新增的技能和移除的技能
            newly_loaded_skills = current_skills - self.last_skills_loaded # 新增的技能
            removed_skills = self.last_skills_loaded - current_skills # 移除的技能

            # 只在技能状态实际发生变化时输出变更日志（优化性能）
            if newly_loaded_skills or removed_skills:
                log.info(f"技能发生变化：新加载的技能：{newly_loaded_skills}，已移除的技能：{removed_skills}")
                # 更新缓存状态
                self.last_skills_loaded = current_skills.copy()
                # 技能变化时情况工具日志记录，确保新技能工具日志能正常输出
                self.logged_skill_tools.clear()

            # --- 2. 根据技能动态构建工具列表
            # 始终包含基础工具（如：load_skill）
            dynamic_tools = self.base_tools.copy()

            # 遍历当前已加载的技能，添加对应的工具
            for skill in current_skills:
                # 获取该技能对应的工具集合
                skill_tools = get_tools_by_skill(skill, self.all_tools)
                if skill_tools:
                    # 为当前技能工具组合生产唯一标识（技能名+工具数量）
                    skill_tools_key = f"{skill}_{len(skill_tools)}"

                    # 确保每个技能工具加载日志只输出一次（避免重复）
                    if skill_tools_key not in self.logged_skill_tools:
                        log.info(f"加载技能'{skill}'的工具，数量：{len(skill_tools)}")
                        self.logged_skill_tools.add(skill_tools_key)

                    # 将技能工具集合添加到动态工具集
                    dynamic_tools.extend(skill_tools)

            # --- 3. 调试信息输出
            # 只有在调试模式下输出详细的工具列表信息
            tool_names = [tool.name for tool in dynamic_tools if hasattr(tool, 'name')]
            log.debug(f"当前可用工具：{tool_names}")

            # --- 4. 系统消息更新
            # 构建反应当前技能状态的提示信息
            skills_prompt = self._build_skills_prompt(current_skills)
            # 更新系统消息，避免提示信息重复积累
            new_system_message = self._update_system_message(request, skills_prompt)

            # --- 5. 请求修改和处理器调用
            # 创建修改后的请求对象，包含过滤后的工具和更新的系统消息
            modified_request = request.override(
                tools=dynamic_tools,
                system_message=new_system_message,
            )

            # 异步调用下一个处理器（可能是下个中间件或者模型调用）
            response = await handler(modified_request)
            return response
        except Exception as e:
            # --- 6. 异常处理
            log.error(f"技能中间件执行错误：{e}", exc_info=True)

            # 优雅降级：出差回退到基础工具集，确保 Agent 基本功能可用
            fallback_request = request.override(tools=self.base_tools)
            return await handler(fallback_request)

    def _build_skills_prompt(self, current_skills: set[str]) -> str:
        """
        构建技能状态提示信息

        参数：
            current_skills: 当前已加载的技能集合

        返回：
            str: 格式化后的技能提示文本
        """
        if not current_skills:
            return "\n## 技能状态\n当前未加载技能，请使用 load_skill 工具加载所有技能"

        # 对技能名称进行排序，确保输出一致性（避免随机顺序）
        skill_list = ", ".join(sorted(current_skills))
        return f"\n\n## 技能状态\n已加载技能：{skill_list}"

    def _update_system_message(self, request: ModelRequest, skills_prompt: str) -> SystemMessage:
        """
        更新系统消息，避免提示信息重复积累

        问题背景：
        - 每次模型调用都会添加技能提示，如果不清理会导致提示信息无限增长，造成 token 浪费和污染上下文

        解决方案：
        1. 检查系统消息内容
        2. 移除旧的技能状体提示部分
        3. 添加新的技能提示部分

        参数：
            request: 当前模型请求对象
            skills_prompt: 新的技能提示文本

        返回：
            SystemMessage: 更新后的系统消息对象
        """
        # 获取当前系统消息对象
        current_system_message = getattr(request, 'system_message', None)
        if current_system_message and hasattr(current_system_message, 'content'):
            # 将当前内容转换成字符串
            current_content = str(current_system_message.content)

            # 按行分割内容，便于逐行处理
            lines = current_content.split('\n')
            clean_lines = [] # 存储清理后的行
            skip_next = False # 标记是否跳过当前行（用于跳过技能状态相关行）

            # 遍历每一行，移除旧的技能状态提示
            for line in lines:
                if line.startswith('## 技能状态'):
                    skip_next = True # 遇到技能状态标题行，开始跳过
                    continue
                if skip_next and line.strip() == "":
                    skip_next = False # 遇到空行，停止跳过
                    continue
                if not skip_next:
                    clean_lines.append(line) # 保留非技能状态行

            # 重新组合清理后的内容
            clean_content = "\n".join(clean_lines).strip()
            # 添加新的技能提示信息
            new_content = clean_content + skills_prompt
        else:
            # 如果没有现有系统消息，直接使用技能提示内容
            new_content = skills_prompt

        # 创建新的系统消息对象
        return SystemMessage(content=new_content)

async def create_skills_based_agent():
    """创建已于 skills 的 agent"""

    # 创建 MCP 客户端获取所有工具
    mcp_client = MultiServerMCPClient({
        # 高德地图MCP服务端 里面有各种高德给你提供公交、地铁、公交、驾车、步行、骑行、POI搜索、IP定位、逆地理编码、云图服务、云图审图、云图审
        "gaode": {
            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/amap-maps/sse",
            "transport": "sse",
            "headers": {
                "Authorization": "Bearer sk-50dd03de53ef4742aa2e7686ea747b67"
            }
        },
        "railway_tools": {
            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/china-railway/sse",
            "transport": "sse",
            "headers": {
                "Authorization": "Bearer sk-50dd03de53ef4742aa2e7686ea747b67"
            }
        }
    })

    gaode_tools = await mcp_client.get_tools(server_name="gaode")
    railway_tools = await mcp_client.get_tools(server_name="railway_tools")

    print(f'所有工具数量 - 高德: {len(gaode_tools)}, 铁路: {len(railway_tools)}')

    # 验证工具名称
    print("工具名称验证:")
    for i, tool in enumerate(gaode_tools + railway_tools):
        tool_name = getattr(tool, 'name', '未知名称')
        print(f"工具 {i + 1}: {tool_name}")

    # 按类别组织的工具集，例如：{"basic_skill": [get_time, get_weather] }
    categorized_tools: dict[str, list[BaseTool]] = {
        "gaode": gaode_tools,
        "12306": railway_tools,
        "python_execution": [python_tools.execute_python, python_tools.run_script],
    }

    graph = create_agent(
        model=deepseek_chat_model,
        tools=[load_skill],
        state_schema=SkillState,
        middleware=[SkillMiddleware(categorized_tools)],
        system_prompt="""
            您是一个多功能智能助手，采用渐进式技能加载架构。
    
            请严格遵循以下工作流程：
            1. 首先分析用户请求属于哪个技能领域
            2. 使用 load_skill 工具加载相应的技能说明
            3. 技能加载后，系统会自动提供该领域的专用工具
            4. 按照技能说明中的指导使用合适的工具
            5. 提供专业、准确的回答
            
            可用技能领域：
            - 高德导航 (gaode_navigation): 地图导航、路径规划
            - 铁路查询 (railway_booking): 火车票查询、预订
            - 数据分析 (data_analysis): 数据统计、分析报告
            - Python脚本 (python_execution): 执行Python代码和脚本
            
            请先加载技能，再使用相应工具！
        """
    )

    return graph

# 创建基于 skills 架构的智能体
graph = asyncio.run(create_skills_based_agent())
