# LangGraph Agent Orchestration Demo
### 「按部就班不偏离」的可控多步智能体工作流

> 把「智能路由 + 知识库检索 + 条件判断 + 大模型推理 + 工具调用 + 记忆回收」做成一台**有状态的状态机**：每一步顺序固定、条件边做护栏，Agent 不许跳、不许偏。

**📌 技术关键词**：LangGraph · Stateful Agent Orchestration · StateGraph · Conditional Edges (Guardrail) · Shared State · RAG Retrieval · Tool Calling · Episodic Memory

---

## 这是什么

一个可运行的 LangGraph Demo，用工业框架复刻了一套自研的「按部就班不偏离」智能体编排。

它解决的工程问题：**普通 Chain 是直线、跑完即焚，无法在中间做「要不要调工具 / 检索不到怎么办」这类分支判断，Agent 容易跑偏。** 本 Demo 用图（Graph）代替链（Chain），让每一步流转都有显式规则和护栏。

## 架构

```
START → retrieve(检索) → judge(判断) ── 条件边 ──┬─ 检索为空 → clarify(追问，不乱编) ─────────► END
                                                  └─ 检索命中 → reason(推理) ── 条件边 ──┬─ 需工具 → call_tool → memorize(回收记忆) ► END
                                                                                        └─ 否则  ─────────────────► memorize ► END
```

| 自研概念 | 行业标准叫法 | 本 Demo 实现 |
|---|---|---|
| 智能路由「按部就班不偏离」 | Stateful Agent Orchestration | `StateGraph` 状态机 |
| LLM×RAG 知识库调取 | Retrieval-Augmented Generation | `retrieve` 节点 |
| 解析→推理→产出 | LLM Reasoning Chain | `reason` 节点 |
| 派给 Agent 的 TOOL | Tool / Function Calling | `call_tool` 节点 |
| Memory 层（召回+沉淀） | Episodic Memory | `memorize` 节点写回 `memory` |
| 不偏离护栏 | Guardrail / Fallback Routing | `judge` 条件边：检索空→`clarify` |

## 怎么跑

默认离线 mock（不依赖任何外部服务，clone 即可运行，先看流程图是否按预期走）：

```bash
pip install -r requirements.txt
python agent_orchestration.py
```

接本地模型网关跑真实模型（需 OpenAI 兼容网关在 `127.0.0.1:8787` 运行）：

```bash
python agent_orchestration.py --real
```

内置两个验证场景，覆盖两条主分支：
- **命中 + 需工具**：`retrieve → judge → reason → call_tool → memorize`
- **未命中**：`retrieve → judge → clarify`（检索为空不进入推理乱答，而是追问补信息）

## 为什么这么做（对照自研）

作者另有一套零依赖自研编排（见 [ai-native-team](https://github.com/Babymrbbbb/ai-native-team)）。本 Demo 是把同一套编排思想用 LangGraph 做的**等价复刻**，用于：
1. 验证自研逻辑与工业标准框架**架构同构**（节点、条件边、共享状态一一对应）。
2. 作为与工业框架的架构同构对照，说明「代码态适合深度定制，框架态适合团队接手」的取舍。

## 诚实边界

- 本仓库为自研编排的工业框架等价实现；**架构设计、节点职责、路由与护栏规则由作者确定，代码由 AI 技术搭子实现。**
- 默认离线 mock 保证 clone 即跑；`--real` 接作者自建本地模型网关。
- `retrieve` 节点真实实现可接 Chroma（`Chroma.as_retriever()`），Demo 内用命中规则演示分支逻辑。

## 仓库结构

```
langgraph-agent-demo/
├── README.md
├── agent_orchestration.py   # LangGraph 状态机（本 Demo 全部逻辑）
├── requirements.txt
└── LICENSE
```

## 体系定位

本仓库是 [ai-native-team](https://github.com/Babymrbbbb/ai-native-team)「AI 原生组织 OS」体系的**编排对照层**组件——把 ai-native-team 的「按部就班不偏离」编排思想，用 LangGraph 工业框架做等价复刻。

> 接入 AI（[sensenova-gateway](https://github.com/Babymrbbbb/sensenova-gateway)）→ 用好 AI（[prompt-craft](https://github.com/Babymrbbbb/prompt-craft)）→ LLM×RAG 知识库（[llm-wiki](https://github.com/Babymrbbbb/llm-wiki)）→ 组织 AI 落地（[ai-native-team](https://github.com/Babymrbbbb/ai-native-team)）→ 交付业务结果（驾驶舱 / 运维工作台）

相关项目：旗舰 [ai-native-team](https://github.com/Babymrbbbb/ai-native-team) · 模型层 [sensenova-gateway](https://github.com/Babymrbbbb/sensenova-gateway) · 方法层 [prompt-craft](https://github.com/Babymrbbbb/prompt-craft) · 知识层 [llm-wiki](https://github.com/Babymrbbbb/llm-wiki) / [kb-cli](https://github.com/Babymrbbbb/kb-cli) · 交付层 [swan-electron-suite](https://github.com/Babymrbbbb/swan-electron-suite)

## License

MIT
