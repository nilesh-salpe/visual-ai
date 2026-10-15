"""Agent framework exercise notebooks: LangChain 1.4.6 and LangGraph 1.2.15, driven by a scripted fake chat model so no API key is needed."""

NBS = []

INSTALL = '%pip install -q "langchain==1.4.6" "langchain-core==1.6.10" "langgraph==1.2.15"'
RUNTIME = 'Everything runs on CPU with a scripted fake chat model, so no API key or GPU is needed. Run the **Install** cell first (pinned to LangChain 1.4.6 and LangGraph 1.2.15).'

FAKE = r'''
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool

class ScriptedChatModel(BaseChatModel):
    """A stand-in for a real chat model: replies with the scripted messages in order (cycling).
    Swap in e.g. init_chat_model("anthropic:claude-sonnet-5-5") to use a real model."""
    script: list
    i: int = 0
    calls: int = 0
    @property
    def _llm_type(self):
        return "scripted"
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self.script[self.i % len(self.script)]
        self.i += 1; self.calls += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])
    def bind_tools(self, tools, **kwargs):
        return self          # a real model would attach the tool schemas to every request

def call(name, args, id):
    """Shorthand for one tool call inside an AIMessage."""
    return {"name": name, "args": args, "id": id}

@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"18°C and sunny in {city}"
'''

# ------------------------------------------------------------------ 01
NBS.append(dict(
    slug='01_langchain_basics', title='01 · LangChain basics: tools, tool calls and the agent loop', deck='agent-frameworks/01-langchain-basics/', deck_name='LangChain basics', minutes=30,
    goals='a tool with a generated JSON schema, an executor that turns tool calls into tool messages (including errors), and the agent loop by hand, then the same agent with `create_agent`.',
    install=INSTALL, runtime=RUNTIME,
    setup=FAKE,
    tasks=[
        dict(fn='build_currency_tool', title='A tool with a schema', md=r'''
            Return a LangChain tool named `convert_currency(amount: float, rate: float) -> float` that multiplies the two numbers. Use the `@tool` decorator: it reads the function name, the **docstring** (which becomes the description the model sees) and the **type hints** (which become the JSON schema).''',
             starter=r'''
            def build_currency_tool():
                # TODO: define convert_currency with @tool, a docstring and type hints, and return it
                raise NotImplementedError''',
             test=r'''
            def _test_build_currency_tool(f):
                t = f()
                assert t.name == "convert_currency", f"tool name is {t.name!r}"
                assert t.description, "add a docstring: it is the description the model reads"
                schema = t.tool_call_schema.model_json_schema()
                assert sorted(schema["required"]) == ["amount", "rate"], f"required args: {schema['required']}"
                assert schema["properties"]["amount"]["type"] == "number", "type-hint amount as float"
                assert t.invoke({"amount": 10, "rate": 0.5}) == 5.0''',
             solution=r'''
            def build_currency_tool_solution():
                @tool
                def convert_currency(amount: float, rate: float) -> float:
                    """Convert an amount of money with an exchange rate."""
                    return amount * rate
                return convert_currency'''),
        dict(fn='run_tool_calls', title='Execute tool calls', md=r'''
            Given an `AIMessage` whose `tool_calls` is a list of `{"name", "args", "id"}` dicts, run each call and return a list of `ToolMessage`s, one per call, **in order**, each with `tool_call_id` set to the call's id.
            * Unknown tool → `ToolMessage(content="Error: unknown tool <name>", status="error", ...)`.
            * A tool that raises → `ToolMessage(content="Error: <exception text>", status="error", ...)`. Returning errors lets the model fix its call instead of crashing the loop.''',
             starter=r'''
            def run_tool_calls(ai_message, tools):
                by_name = {t.name: t for t in tools}
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_run_tool_calls(f):
                @tool
                def divide(a: float, b: float) -> float:
                    """Divide a by b."""
                    return a / b
                ai = AIMessage(content="", tool_calls=[call("get_weather", {"city": "Paris"}, "t1"), call("divide", {"a": 1, "b": 0}, "t2"), call("nope", {}, "t3")])
                out = f(ai, [get_weather, divide])
                assert [m.tool_call_id for m in out] == ["t1", "t2", "t3"], "one ToolMessage per call, in order"
                assert all(isinstance(m, ToolMessage) for m in out)
                assert out[0].content == "18°C and sunny in Paris" and out[0].status == "success"
                assert out[1].status == "error" and "division" in out[1].content, "return the exception text as an error result"
                assert out[2].status == "error" and "unknown tool" in out[2].content''',
             solution=r'''
            def run_tool_calls_solution(ai_message, tools):
                by_name = {t.name: t for t in tools}
                out = []
                for tc in ai_message.tool_calls:
                    t = by_name.get(tc["name"])
                    if t is None:
                        out.append(ToolMessage(content=f"Error: unknown tool {tc['name']}", tool_call_id=tc["id"], status="error"))
                        continue
                    try:
                        out.append(ToolMessage(content=str(t.invoke(tc["args"])), tool_call_id=tc["id"], name=tc["name"]))
                    except Exception as e:
                        out.append(ToolMessage(content=f"Error: {e}", tool_call_id=tc["id"], status="error"))
                return out'''),
        dict(fn='agent_loop', title='The agent loop by hand', md=r'''
            Write the loop from the "What an agent is" deck: start with `[HumanMessage(question)]`, call `model.invoke(messages)`, append the reply; if it has no `tool_calls`, return the messages; otherwise append the tool results (use your `run_tool_calls`) and go again. Raise `RuntimeError` after `max_steps` model calls without a final answer.''',
             starter=r'''
            def agent_loop(model, tools, question, max_steps=5):
                model = model.bind_tools(tools)
                messages = [HumanMessage(question)]
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_agent_loop(f):
                m = ScriptedChatModel(script=[AIMessage(content="", tool_calls=[call("get_weather", {"city": "Oslo"}, "a")]), AIMessage(content="Oslo: 18°C.")])
                msgs = f(m, [get_weather], "Weather in Oslo?")
                kinds = [type(x).__name__ for x in msgs]
                assert kinds == ["HumanMessage", "AIMessage", "ToolMessage", "AIMessage"], kinds
                assert msgs[2].content == "18°C and sunny in Oslo" and msgs[-1].content == "Oslo: 18°C."
                looping = ScriptedChatModel(script=[AIMessage(content="", tool_calls=[call("get_weather", {"city": "X"}, "x")])])
                try:
                    f(looping, [get_weather], "?", max_steps=3)
                    assert False, "a model that never stops must hit the step limit"
                except RuntimeError:
                    pass
                assert looping.calls == 3, f"expected exactly 3 model calls, got {looping.calls}"''',
             solution=r'''
            def agent_loop_solution(model, tools, question, max_steps=5):
                model = model.bind_tools(tools)
                messages = [HumanMessage(question)]
                for _ in range(max_steps):
                    ai = model.invoke(messages)
                    messages.append(ai)
                    if not ai.tool_calls:
                        return messages
                    messages += run_tool_calls_solution(ai, tools)
                raise RuntimeError("step limit reached")'''),
    ],
    explore_md='The same agent with `create_agent`: it compiles a LangGraph graph with a `model` node and a `tools` node and runs the loop you just wrote.',
    explore=r'''
from langchain.agents import create_agent
m = ScriptedChatModel(script=[AIMessage(content="", tool_calls=[call("get_weather", {"city": "Paris"}, "t1")]), AIMessage(content="It is 18°C in Paris.")])
agent = create_agent(m, [get_weather], system_prompt="You are a helpful assistant.")
out = agent.invoke({"messages": [HumanMessage("Weather in Paris?")]})
for msg in out["messages"]:
    print(f"{type(msg).__name__:13}", msg.content or msg.tool_calls)
print("graph nodes:", list(agent.get_graph().nodes))''',
    takeaways='''
        * A tool is a function plus a **schema and description** the model reads; the docstring is part of your prompt.
        * The model never runs code: it returns structured **tool calls**; your code executes them and returns **tool messages** tied by id.
        * `create_agent` is the same loop, compiled as a LangGraph graph, with middleware hooks around model and tool calls.''',
))

# ------------------------------------------------------------------ 02
NBS.append(dict(
    slug='02_langgraph_core', title='02 · LangGraph core: state, reducers, edges and a ReAct graph', deck='agent-frameworks/02-langgraph-core/', deck_name='LangGraph core', minutes=35,
    goals='a custom state reducer, a graph with a conditional edge, and the ReAct agent as a two-node graph with `ToolNode` and `tools_condition`.',
    install=INSTALL, runtime=RUNTIME,
    setup=FAKE + r'''
import operator, re
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
''',
    tasks=[
        dict(fn='keep_last', title='A reducer that keeps the last k items', md=r'''
            Each state key has a **reducer** that merges a node's update into the current value. The default overwrites; `operator.add` appends lists. Write `keep_last(k)`, returning a reducer `(left, right) -> list` that concatenates and keeps only the last `k` items (a crude sliding window for history).''',
             starter=r'''
            def keep_last(k):
                # TODO: return a function (left, right) -> list
                raise NotImplementedError''',
             test=r'''
            def _test_keep_last(f):
                r = f(3)
                assert r([1, 2], [3, 4]) == [2, 3, 4] and r([], [1]) == [1]
                class S(TypedDict):
                    log: Annotated[list, f(3)]
                g = StateGraph(S)
                for name in "abcd":
                    g.add_node(name, lambda s, name=name: {"log": [name]})
                g.add_edge(START, "a"); g.add_edge("a", "b"); g.add_edge("b", "c"); g.add_edge("c", "d"); g.add_edge("d", END)
                assert g.compile().invoke({"log": []})["log"] == ["b", "c", "d"], "the graph should keep only the last 3 entries"''',
             solution=r'''
            def keep_last_solution(k):
                def reducer(left, right):
                    return (list(left or []) + list(right or []))[-k:]
                return reducer'''),
        dict(fn='build_router_graph', title='Routing with a conditional edge', md=r'''
            Build and **compile** a graph over the state below. Node `classify` sets `route` to `"math"` if the question contains a digit, else `"chat"`. A **conditional edge** from `classify` goes to node `math` (answer: `"sum=<sum of the integers in the question>"`) or node `chat` (answer: `"Hello!"`). Both end at `END`.''',
             starter=r'''
            class RouteState(TypedDict):
                question: str
                route: str
                answer: str

            def build_router_graph():
                g = StateGraph(RouteState)
                # TODO: nodes classify, math, chat; START -> classify; conditional edge; math/chat -> END
                raise NotImplementedError''',
             test=r'''
            def _test_build_router_graph(f):
                app = f()
                r = app.invoke({"question": "add 2 and 40", "route": "", "answer": ""})
                assert r["route"] == "math" and r["answer"] == "sum=42", r
                r = app.invoke({"question": "hi there", "route": "", "answer": ""})
                assert r["route"] == "chat" and r["answer"] == "Hello!", r
                assert {"classify", "math", "chat"} <= set(app.get_graph().nodes)''',
             solution=r'''
            def build_router_graph_solution():
                g = StateGraph(RouteState)
                g.add_node("classify", lambda s: {"route": "math" if re.search(r"\d", s["question"]) else "chat"})
                g.add_node("math", lambda s: {"answer": f"sum={sum(map(int, re.findall(r'\d+', s['question'])))}"})
                g.add_node("chat", lambda s: {"answer": "Hello!"})
                g.add_edge(START, "classify")
                g.add_conditional_edges("classify", lambda s: s["route"], {"math": "math", "chat": "chat"})
                g.add_edge("math", END); g.add_edge("chat", END)
                return g.compile()'''),
        dict(fn='build_react_graph', title='The ReAct agent as a graph', md=r'''
            Build the agent loop as a graph over `MessagesState` (its `messages` key uses the `add_messages` reducer, which appends and de-duplicates by id):
            * node `agent`: call `model.bind_tools(tools).invoke(state["messages"])` and return `{"messages": [reply]}`;
            * node `tools`: `ToolNode(tools)`, which runs every tool call in the last message;
            * `START → agent`; a conditional edge from `agent` with `tools_condition` (goes to `"tools"` if there are tool calls, else to `END`); `tools → agent`.''',
             starter=r'''
            def build_react_graph(model, tools):
                g = StateGraph(MessagesState)
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_build_react_graph(f):
                m = ScriptedChatModel(script=[AIMessage(content="", tool_calls=[call("get_weather", {"city": "Rome"}, "r1")]), AIMessage(content="Rome: 18°C.")])
                app = f(m, [get_weather])
                out = app.invoke({"messages": [HumanMessage("Weather in Rome?")]})
                kinds = [type(x).__name__ for x in out["messages"]]
                assert kinds == ["HumanMessage", "AIMessage", "ToolMessage", "AIMessage"], kinds
                assert out["messages"][2].content == "18°C and sunny in Rome"
                assert {"agent", "tools"} <= set(app.get_graph().nodes)''',
             solution=r'''
            def build_react_graph_solution(model, tools):
                bound = model.bind_tools(tools)
                g = StateGraph(MessagesState)
                g.add_node("agent", lambda s: {"messages": [bound.invoke(s["messages"])]})
                g.add_node("tools", ToolNode(tools))
                g.add_edge(START, "agent")
                g.add_conditional_edges("agent", tools_condition)
                g.add_edge("tools", "agent")
                return g.compile()'''),
    ],
    explore_md='Stream the per-node updates of the ReAct graph, and print the graph as Mermaid text (paste it into any Mermaid viewer).',
    explore=r'''
m = ScriptedChatModel(script=[AIMessage(content="", tool_calls=[call("get_weather", {"city": "Rome"}, "r1")]), AIMessage(content="Rome: 18°C.")])
app = build_react_graph_solution(m, [get_weather])
for update in app.stream({"messages": [HumanMessage("Weather in Rome?")]}, stream_mode="updates"):
    for node, value in update.items():
        print(f"{node:6} ->", [type(x).__name__ for x in value["messages"]])
print(app.get_graph().draw_mermaid())''',
    takeaways='''
        * State is a typed dict; each key has a **reducer** (default: overwrite). Nodes return **partial updates**, never the whole state.
        * Edges are fixed, **conditional edges** call a routing function; `END` stops the run.
        * The ReAct agent is just `agent ⇄ tools` with `tools_condition` deciding when to stop.''',
))

# ------------------------------------------------------------------ 03
NBS.append(dict(
    slug='03_langgraph_production', title='03 · LangGraph in production: checkpoints, threads, interrupts and resuming', deck='agent-frameworks/03-langgraph-production/', deck_name='LangGraph in production', minutes=35,
    goals='per-thread state with a checkpointer, a human approval step with `interrupt()` and `Command(resume=...)`, and resuming a failed run from its last checkpoint without redoing finished steps.',
    install=INSTALL, runtime=RUNTIME,
    setup=r'''
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

def thread(tid):
    """The config that selects a conversation thread in the checkpointer."""
    return {"configurable": {"thread_id": tid}}
''',
    tasks=[
        dict(fn='build_counter_app', title='Threads and checkpoints', md=r'''
            Build a one-node graph over `CounterState` whose node `bump` adds 1 to `count` (the key's reducer is `operator.add`, so return `{"count": 1}`). Compile it **with an `InMemorySaver` checkpointer**. Each `thread_id` then keeps its own state across `invoke` calls.''',
             starter=r'''
            class CounterState(TypedDict):
                count: Annotated[int, operator.add]

            def build_counter_app():
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_build_counter_app(f):
                app = f()
                app.invoke({"count": 0}, thread("a")); r = app.invoke({"count": 0}, thread("a"))
                assert r["count"] == 2, f"thread a should remember its count across calls, got {r['count']}"
                assert app.invoke({"count": 0}, thread("b"))["count"] == 1, "thread b starts fresh"
                assert app.get_state(thread("a")).values["count"] == 2
                assert len(list(app.get_state_history(thread("a")))) >= 4, "every step leaves a checkpoint"''',
             solution=r'''
            def build_counter_app_solution():
                g = StateGraph(CounterState)
                g.add_node("bump", lambda s: {"count": 1})
                g.add_edge(START, "bump"); g.add_edge("bump", END)
                return g.compile(checkpointer=InMemorySaver())'''),
        dict(fn='build_approval_app', title='Human approval with interrupt()', md=r'''
            Build `plan → approve → (execute | cancel) → END` over `ApprovalState`, compiled with a checkpointer:
            * `plan` sets `action` to `"delete_branch"`;
            * `approve` calls `interrupt({"action": state["action"]})` and stores the returned value in `approved`;
            * a conditional edge goes to `execute` (sets `status="executed"` and appends the action to the global `EXECUTED` list) or `cancel` (sets `status="cancelled"`).

            ⚠️ When resumed, the **whole `approve` node runs again from the top**, so never put the side effect before the `interrupt()` call.''',
             starter=r'''
            EXECUTED = []

            class ApprovalState(TypedDict):
                action: str
                approved: bool
                status: str

            def build_approval_app():
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_build_approval_app(f):
                EXECUTED.clear()
                app = f()
                r = app.invoke({"action": "", "approved": False, "status": ""}, thread("ok"))
                assert "__interrupt__" in r, "the run should pause at the approval step"
                assert r["__interrupt__"][0].value == {"action": "delete_branch"}
                assert app.get_state(thread("ok")).next == ("approve",)
                r = app.invoke(Command(resume=True), thread("ok"))
                assert r["status"] == "executed" and EXECUTED == ["delete_branch"], (r, EXECUTED)
                app.invoke({"action": "", "approved": False, "status": ""}, thread("no"))
                r = app.invoke(Command(resume=False), thread("no"))
                assert r["status"] == "cancelled" and EXECUTED == ["delete_branch"], "a rejected action must not run"''',
             solution=r'''
            def build_approval_app_solution():
                g = StateGraph(ApprovalState)
                g.add_node("plan", lambda s: {"action": "delete_branch"})
                g.add_node("approve", lambda s: {"approved": bool(interrupt({"action": s["action"]}))})
                def execute(s):
                    EXECUTED.append(s["action"])
                    return {"status": "executed"}
                g.add_node("execute", execute)
                g.add_node("cancel", lambda s: {"status": "cancelled"})
                g.add_edge(START, "plan"); g.add_edge("plan", "approve")
                g.add_conditional_edges("approve", lambda s: "execute" if s["approved"] else "cancel")
                g.add_edge("execute", END); g.add_edge("cancel", END)
                return g.compile(checkpointer=InMemorySaver())'''),
        dict(fn='run_with_resume', title='Resume after a crash', md=r'''
            With a checkpointer, a failed run keeps the checkpoints of the steps that finished. Invoking the same thread with input `None` **continues from the last checkpoint** instead of starting over. Write `run_with_resume(app, inputs, config, max_restarts=3)`: invoke; on an exception, re-invoke with `None` (up to `max_restarts` times); return `(result, restarts)`. Re-raise if it still fails.''',
             starter=r'''
            def run_with_resume(app, inputs, config, max_restarts=3):
                # TODO
                raise NotImplementedError''',
             test=r'''
            def _test_run_with_resume(f):
                calls = {"fetch": 0, "flaky": 0}
                class S(TypedDict):
                    log: Annotated[list, operator.add]
                def fetch(s):
                    calls["fetch"] += 1
                    return {"log": ["fetched"]}
                def flaky(s):
                    calls["flaky"] += 1
                    if calls["flaky"] < 3:
                        raise ConnectionError("upstream timed out")
                    return {"log": ["processed"]}
                g = StateGraph(S); g.add_node("fetch", fetch); g.add_node("flaky", flaky)
                g.add_edge(START, "fetch"); g.add_edge("fetch", "flaky"); g.add_edge("flaky", END)
                app = g.compile(checkpointer=InMemorySaver())
                result, restarts = f(app, {"log": []}, thread("job"))
                assert result["log"] == ["fetched", "processed"] and restarts == 2, (result, restarts)
                assert calls["fetch"] == 1, "a finished step must not run again after a restart"
                calls.update(fetch=0, flaky=-10)
                try:
                    f(app, {"log": []}, thread("job2"), max_restarts=1)
                    assert False, "should re-raise after max_restarts"
                except ConnectionError:
                    pass''',
             solution=r'''
            def run_with_resume_solution(app, inputs, config, max_restarts=3):
                restarts = 0
                while True:
                    try:
                        return app.invoke(inputs if restarts == 0 else None, config), restarts
                    except Exception:
                        if restarts >= max_restarts:
                            raise
                        restarts += 1'''),
    ],
    explore_md='Every step leaves a checkpoint. Walk a thread\'s history (newest first): this is what "time travel" and debugging replay are built on.',
    explore=r'''
app = build_approval_app_solution()
app.invoke({"action": "", "approved": False, "status": ""}, thread("demo"))
app.invoke(Command(resume=True), thread("demo"))
for snap in app.get_state_history(thread("demo")):
    print(f"step {snap.metadata.get('step'):>2}  next={snap.next!s:14} status={snap.values.get('status')!r}")''',
    takeaways='''
        * A **checkpointer** saves state after every step, per **thread**; this gives memory, resumption after failure, and history.
        * `interrupt()` pauses a run until `Command(resume=value)`; the node **re-runs from its start**, so side effects go after the interrupt or in a later node.
        * In production use a durable checkpointer (e.g. Postgres) instead of `InMemorySaver`, and make nodes idempotent.''',
))
