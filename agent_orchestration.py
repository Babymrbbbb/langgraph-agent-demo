"""D3 作品集 Demo：用 LangGraph 复刻你自研的「按部就班不偏离」工作流编排。

【这是给面试官看的作品，不是让你手写的】
你的自研架构（ai-native-team）里，智能路由的本质是：
    Agent 结合 SKILL / TOOL / LLM&RAG 检索去干活，且每一步都不许跳、不许偏。
这正是 LangGraph 的主场——把工作流变成一台「有状态的状态机」：
    - Node（节点）  = 每一步动作（检索 / 判断 / 推理 / 调工具 / 回收记忆）
    - Edge（边）    = 流转条件（检索为空→追问；命中→推理；需工具→调工具）
    - State（状态） = 一块全局黑板，所有节点共享读写——这就是「不偏离」的锚

运行（默认离线 mock，不依赖网关，先看流程图是否按预期走）：
    python agent_orchestration.py
接真实网关跑（需要 127.0.0.1:8787 在运行）：
    python agent_orchestration.py --real
"""

import argparse
from typing import TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, START, END

# 若接真实网关，用 LangChain 的 ChatOpenAI 指向你的零依赖网关
try:
    from langchain_openai import ChatOpenAI
except Exception:  # 离线 mock 模式不需要
    ChatOpenAI = None


# ============================ 全局状态（黑板） ============================
class State(TypedDict):
    question: str            # 用户问题（入口）
    retrieved: str           # 检索到的资料（RAG 召回）
    answer: str              # 模型推理产出
    needs_tool: bool         # 是否需要调用工具
    tool_result: str         # 工具返回
    memory: Annotated[list, operator.add]   # 回收记忆（= 你的 Memory 层：沉淀）
    trace: Annotated[list, operator.add]    # 执行轨迹（证明「按部就班不偏离」）


# ============================ 真实 / Mock 切换 ============================
USE_MOCK = True
if not USE_MOCK and ChatOpenAI is not None:
    llm = ChatOpenAI(
        model="deepseek-v4-flash",
        base_url="http://127.0.0.1:8787/v1",
        api_key="local",
        temperature=0.3,
    )


def reason_with_llm(question: str, context: str) -> str:
    """真实推理：把资料拼进提示词，调网关模型。"""
    if USE_MOCK or ChatOpenAI is None:
        # 离线占位：命中资料就给运营建议，并标记是否需工具
        if context:
            return ("基于知识库资料，建议：① 收银话术引导出示 ② 权益前置展示 "
                    "③ 店长看板追踪转化。若需落地，可生成一张门店动作清单（将调用工具）。")
        return "通用运营建议：先定位门店类型与时段，再定抓手。"
    prompt = (
        "你是烘焙连锁运营参谋。\n资料：{ctx}\n问题：{q}\n"
        "请给出可执行动作建议；若需生成具体清单，请在末尾写「[需工具]」。"
    ).format(ctx=context, q=question)
    return llm.invoke(prompt).content


# ============================ 节点（= 你架构里的每一步） ============================
def retrieve(state: State) -> dict:
    """节点1 · 检索：= 你的 LLM×RAG 知识库调取。
    真实实现：Chroma.as_retriever().invoke(state['question'])。这里用 mock 命中规则演示。"""
    q = state["question"]
    # mock：问题含「会员」视为知识库有资料，否则空（触发追问分支）
    docs = ("资料：会员运营提升三招——① 收银话术 ② 权益前置 ③ 数据看板。"
            if "会员" in q else "")
    return {"retrieved": docs, "trace": ["1.retrieve 检索"]}


def judge(state: State) -> dict:
    """节点2 · 判断：纯路由节点，不产出，只决定下一步往哪走。"""
    return {"trace": ["2.judge 判断"]}


def clarify(state: State) -> dict:
    """分支A · 追问：检索为空时，不让 Agent 瞎编，而是回收用户补信息（= 你的「不偏离」护栏）。"""
    q = state["question"]
    return {"answer": f"知识库未找到「{q}」相关资料，请补充：场景 / 门店 / 时间范围？",
            "trace": ["→ clarify 追问"]}


def reason(state: State) -> dict:
    """节点3 · 推理：= 你的「解析→推理→产出」。同时判断是否需调用工具。"""
    ans = reason_with_llm(state["question"], state["retrieved"])
    needs = ("清单" in state["question"]) or ("[需工具]" in ans)
    return {"answer": ans, "needs_tool": needs, "trace": ["3.reason 推理"]}


def call_tool(state: State) -> dict:
    """分支B · 调工具：= 你派给 Agent 的 TOOL。这里 mock 一个「生成门店动作清单」工具。"""
    q = state["question"]
    plan = (f"工具产出·门店动作清单（针对「{q}」）：\n"
            "  - 门店A：早班话术培训 + 权益码台卡\n"
            "  - 门店B：会员日双倍积分 + 企微提醒\n"
            "  - 门店C：店长看板新增出示率指标")
    return {"tool_result": plan, "trace": ["→ call_tool 调工具"]}


def memorize(state: State) -> dict:
    """节点4 · 回收记忆：= 你的 Memory 层。把本轮 Q+A 沉淀，供后续轮次复用。"""
    entry = {"q": state["question"], "a": state["answer"]}
    return {"memory": [entry], "trace": ["4.memorize 回收记忆"]}


# ============================ 条件路由（= 你的智能路由规则） ============================
def route_after_judge(state: State) -> str:
    """检索为空 → 追问；命中 → 推理。这就是「不偏离」的硬规则。"""
    return "clarify" if not state["retrieved"] else "reason"


def route_after_reason(state: State) -> str:
    """需工具 → 调工具；否则直接回收记忆收尾。"""
    return "call_tool" if state.get("needs_tool") else "memorize"


# ============================ 组装状态机 ============================
def build_graph():
    g = StateGraph(State)
    g.add_node("retrieve", retrieve)
    g.add_node("judge", judge)
    g.add_node("clarify", clarify)
    g.add_node("reason", reason)
    g.add_node("call_tool", call_tool)
    g.add_node("memorize", memorize)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "judge")
    g.add_conditional_edges("judge", route_after_judge,
                            {"clarify": "clarify", "reason": "reason"})
    g.add_conditional_edges("reason", route_after_reason,
                            {"call_tool": "call_tool", "memorize": "memorize"})
    g.add_edge("clarify", END)
    g.add_edge("call_tool", "memorize")
    g.add_edge("memorize", END)
    return g.compile()


def run_one(app, question: str):
    init = {"question": question, "retrieved": "", "answer": "",
            "needs_tool": False, "tool_result": "", "memory": [], "trace": []}
    out = app.invoke(init)
    print("=" * 60)
    print("问题：", question)
    print("执行轨迹（按部就班，顺序固定）：")
    for step in out["trace"]:
        print("   ", step)
    print("最终回答：", out["answer"])
    if out.get("tool_result"):
        print("工具结果：\n", out["tool_result"])
    print("回收记忆条目数：", len(out["memory"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="接 127.0.0.1:8787 网关跑真实模型")
    args = parser.parse_args()
    if args.real:
        USE_MOCK = False

    app = build_graph()
    # 场景1：命中 + 需工具（走 retrieve→judge→reason→call_tool→memorize）
    run_one(app, "会员运营怎么提升？给我一份门店动作清单")
    # 场景2：未命中（走 retrieve→judge→clarify，不偏离、不乱答）
    run_one(app, "宇宙飞船烤炉怎么配？")
