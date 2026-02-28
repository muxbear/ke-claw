# 定义简单工具
from typing import Annotated

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.types import Command

from agent.skills_list import SKILLS
from agent.utils.log_util import log


@tool
def load_skill(skill_name: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """
    根据技能名称从技能列表中查找技能，并将技能的完整内容加载到上下文中
    Args:
        skill_name: str 技能名称
        tool_call_id: Annotated[str, InjectedToolCallId] 工具调用ID

    Returns:
        技能的全部内容
    """

    for skill in SKILLS:
        if skill_name == skill["name"]:
            log.info(f"技能加载成功: {skill_name}")
            return Command(
                update={
                    "messages": [
                        ToolMessage(content=f"已经加载技能：{skill_name} \n\n {skill['description']} \n\n {skill['content']}",
                                    tool_call_id=tool_call_id),
                    ],
                    "skills_loaded": [skill_name]
                }
            )

    # 未找到技能
    available = ", ".join(s["name"] for s in SKILLS)
    log.warning(f"技能未找到: {skill_name}，可用技能: {available}")
    return Command(
        update={
            "messages": [ToolMessage(
                content=f"未找到技能 '{skill_name}'。可用技能: {available}",
                tool_call_id=tool_call_id
            )]
        }
    )
