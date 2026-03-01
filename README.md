KE Claw - 知识工程智能代理

KE Claw 是一个基于 [LangGraph](https://github.com/langchain-ai/langgraph) 和 [Anthropic Agent Skills](https://agentskills.io) 规范构建的智能代理系统，采用渐进式工具加载架构。

 核心特性
- **渐进式工具加载**: 采用 SkillMiddleware 中间件，根据用户需求动态加载对应技能的工具

- **Agent Skills 规范**: 遵循 Anthropic Agent Skills 规范，使用 SKILL.md 定义技能

- **MCP 工具集成**: 通过 MCP (Model Context Protocol) 集成高德地图、12306 铁路等外部服务

- **动态技能发现**: 支持从 skills/ 目录自动发现和加载新技能 

技术架构
  ┌─────────────────────────────────────────────────────────┐
  │                    LangGraph Agent                       │
  ├─────────────────────────────────────────────────────────┤
  │  SkillMiddleware (渐进式工具加载)                        │
  │  ┌─────────────┬─────────────┬─────────────┐           │
  │  │ gaode_navi │ railway     │ python      │           │
  │  │ gation     │ _booking    │ _execution  │           │
  │  └─────────────┴─────────────┴─────────────┘           │
  ├─────────────────────────────────────────────────────────┤
  │  MCP Tools: 高德地图 | 12306铁路 | Python执行器        │
  ├─────────────────────────────────────────────────────────┤
  │  LLM: DeepSeek Chat                                     │
  └─────────────────────────────────────────────────────────┘

## 快速开始
### 环境要求
- Python 3.10+
- DeepSeek API Key
### 安装步骤
1. 克隆项目并安装依赖

   ``` cmd
   cd ke-claw
   pip install -e . "langgraph-cli[inmem]"
   ```

2. 配置环境变量
  ``` cmd
  cp .env.example .env
  ```

  编辑 .env 文件，添加必要的 API Key:
# DeepSeek API Key
DEEPSEEK_API_KEY=your_deepseek_api_key
# (可选) LangSmith 追踪
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_TRACING=true

3. 启动服务

  ``` cmd
  langgraph dev
  ```

  启动成功后，访问 LangGraph Studio (默认 http://localhost:4200) 开始使用。
  功能说明
  可用技能
| 技能名称 | 功能描述 | 工具数量 |
|---------|---------|---------|
| gaode_navigation | 高德地图：天气查询、地图搜索、路线规划 | MCP 工具 |
| railway_booking | 12306铁路：车站查询、车票查询、时刻表 | MCP 工具 |
| python_execution | Python脚本：代码执行、预定义脚本 | 2 个工具 |
| data_analysis | 数据分析：数据处理、统计分析 | (扩展中) |
技能加载机制
KE Claw 采用渐进式工具加载架构：
1. 初始状态: Agent 只加载基础工具 (load_skill)

2. 技能加载: 用户请求触发 load_skill 工具，加载对应技能

3. 动态工具: SkillMiddleware 根据已加载的技能，动态提供对应工具

4. 按需加载: 只加载当前任务所需的工具，避免"工具过多降智"问题
    使用示例
    用户: 查询北京到上海的高铁票
    Agent: 

5. 加载 railway_booking 技能

6. 调用 get-station-code-of-citys 获取北京、上海的 station_code

7. 调用 get-current-date 获取当前日期

8. 调用 get-tickets 查询高铁票

9. 返回查询结果
    开发指南
    添加新技能

10. 在 skills/ 目录下创建新技能目录

  ``` cmd
  skills/
  └── my_skill/
   ├── SKILL.md          # 必需：技能定义
   ├── scripts/          # 可选：预定义脚本
   ├── references/       # 可选：参考资料
   └── assets/          # 可选：静态资源
  ```

11. 编写 SKILL.md

``` text
---
name: my_skill
description: 技能描述，说明何时使用此技能
---

# 技能说明
技能的具体使用指南...
```

3. 在 graph.py 中注册技能工具
  ``` python
  categorized_tools: dict[str, list[BaseTool]] = {
   "my_skill": [my_tool1, my_tool2],
  }
  ```
4. 重启服务，新技能自动加载
运行测试
# 运行单元测试
``` cmd
make test
```

# 运行集成测试
``` cmd
make integration_tests
```

# 运行测试并监听文件变化
``` cmd
make test_watch
```

代码规范

- 遵循 PEP 8
- 使用 ruff 进行代码检查和格式化
- 使用 mypy --strict 进行类型检查
- 参考 AGENTS.md 了解详细规范
项目结构
ke-claw/
├── src/agent/                 # 核心代码
│   ├── graph.py              # LangGraph 定义
│   ├── skills_loader.py      # 技能动态加载器
│   ├── custom_llm.py         # LLM 配置
│   └── utils/
│       ├── tools.py          # 工具定义
│       └── python_tools.py   # Python 执行工具
├── skills/                    # Agent Skills
│   ├── gaode_navigation/
│   ├── railway_booking/
│   ├── python_execution/
│   └── data_analysis/
├── tests/                     # 测试
│   ├── unit_tests/
│   └── integration_tests/
├── AGENTS.md                  # AI 代理开发指南
├── Makefile                   # 开发命令
└── pyproject.toml             # 项目配置
相关链接
- LangGraph 文档 (https://langchain-ai.github.io/langgraph/)
- Anthropic Agent Skills 规范 (https://agentskills.io)
- LangGraph Server 教程 (https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/)
- LangSmith 追踪平台 (https://smith.langchain.com/)
许可证
MIT License