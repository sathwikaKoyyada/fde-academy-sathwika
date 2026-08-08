from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict

model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

test_complaints = [
    "Account #48213 - My internet has been down for 6 hours and I work from home. This is costing me money. Fix this NOW.",
    "Ticket #9042 - Billing seems slightly higher this month than usual, could someone check when convenient? No rush.",
    "Account #77410 - Complete outage across my whole building, multiple neighbors affected, please escalate immediately.",
    "Just wanted to say the new app update looks nice. Ticket #201.",
]

# ---- chains (from Exercise 1) ----
classify_prompt = ChatPromptTemplate.from_template(
    "Classify this customer complaint as exactly one word: URGENT or ROUTINE. "
    "Respond with only that word, nothing else.\n\nComplaint: {complaint}"
)
extract_prompt = ChatPromptTemplate.from_template(
    "Extract the account or ticket ID number from this complaint. "
    "Respond with only the ID (digits), nothing else.\n\nComplaint: {complaint}"
)
summarize_prompt = ChatPromptTemplate.from_template(
    "Summarize this complaint in exactly one sentence.\n\nComplaint: {complaint}"
)
work_order_prompt = ChatPromptTemplate.from_template(
    "Draft a brief work order (2-3 sentences): what needs to happen, for account {account_id}, "
    "at what priority, based on this complaint.\n\nComplaint: {complaint}"
)

classify_chain = classify_prompt | model | StrOutputParser()
extract_chain = extract_prompt | model | StrOutputParser()
summarize_chain = summarize_prompt | model | StrOutputParser()
work_order_chain = work_order_prompt | model | StrOutputParser()


# ---- Task 1: state + nodes ----
class ComplaintState(TypedDict):
    complaint: str
    classification: str
    account_id: str
    summary: str
    proposed_work_order: str
    status: str


def classify_node(state):
    return {
        **state,
        "classification": classify_chain.invoke(
            {"complaint": state["complaint"]}
        ).strip(),
    }


def extract_node(state):
    return {
        **state,
        "account_id": extract_chain.invoke({"complaint": state["complaint"]}).strip(),
    }


def summarize_node(state):
    return {
        **state,
        "summary": summarize_chain.invoke({"complaint": state["complaint"]}).strip(),
    }


def propose_work_order_node(state):
    wo = work_order_chain.invoke(
        {"complaint": state["complaint"], "account_id": state["account_id"]}
    )
    return {**state, "proposed_work_order": wo, "status": "pending_approval"}


def dispatch_node(state):
    return {**state, "status": "dispatched"}


def route_after_classify(state):
    return "extract" if state["classification"] == "URGENT" else "summarize"


# ---- Task 2: wire graph with interrupt ----
graph = StateGraph(ComplaintState)
graph.add_node("classify", classify_node)
graph.add_node("extract", extract_node)
graph.add_node("summarize", summarize_node)
graph.add_node("propose_work_order", propose_work_order_node)
graph.add_node("dispatch", dispatch_node)

graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify", route_after_classify, {"extract": "extract", "summarize": "summarize"}
)
graph.add_edge("extract", "propose_work_order")
graph.add_edge("propose_work_order", "dispatch")
graph.add_edge("dispatch", END)
graph.add_edge("summarize", END)

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer, interrupt_before=["dispatch"])

config = {"configurable": {"thread_id": "complaint-001"}}
init_state = {
    "complaint": test_complaints[0],
    "classification": "",
    "account_id": "",
    "summary": "",
    "proposed_work_order": "",
    "status": "",
}

print("--- Task 2: first invoke (should pause before dispatch) ---")
result = app.invoke(init_state, config)
print(result)

# ---- Task 3: approve & resume ----
print("\n--- Task 3: pending approval ---")
current_state = app.get_state(config)
print("PENDING APPROVAL:", current_state.values["proposed_work_order"])

print("\n--- Task 3: resume ---")
final = app.invoke(None, config)
print(final)
assert final["status"] == "dispatched"
print("\nstatus confirmed: dispatched")
