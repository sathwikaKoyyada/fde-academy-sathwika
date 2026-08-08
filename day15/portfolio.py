import time, re
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

# ============================================================
# EXERCISE 1: Classify -> Extract -> Summarize
# ============================================================
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


print("=" * 60)
print("EXERCISE 1: Classify -> Extract -> Summarize")
print("=" * 60)

ex1_graph = StateGraph(ComplaintState)
ex1_graph.add_node("classify", classify_node)
ex1_graph.add_node("extract", extract_node)
ex1_graph.add_node("summarize", summarize_node)
ex1_graph.set_entry_point("classify")
ex1_graph.add_conditional_edges(
    "classify", route_after_classify, {"extract": "extract", "summarize": "summarize"}
)
ex1_graph.add_edge("extract", END)
ex1_graph.add_edge("summarize", END)
ex1_app = ex1_graph.compile()

for complaint in test_complaints:
    result = ex1_app.invoke(
        {
            "complaint": complaint,
            "classification": "",
            "account_id": "",
            "summary": "",
            "proposed_work_order": "",
            "status": "",
        }
    )
    print(result)

# ============================================================
# EXERCISE 2: Human Approval Gate on Work Orders
# ============================================================
print("\n" + "=" * 60)
print("EXERCISE 2: Human Approval Step")
print("=" * 60)

ex2_graph = StateGraph(ComplaintState)
ex2_graph.add_node("classify", classify_node)
ex2_graph.add_node("extract", extract_node)
ex2_graph.add_node("summarize", summarize_node)
ex2_graph.add_node("propose_work_order", propose_work_order_node)
ex2_graph.add_node("dispatch", dispatch_node)
ex2_graph.set_entry_point("classify")
ex2_graph.add_conditional_edges(
    "classify", route_after_classify, {"extract": "extract", "summarize": "summarize"}
)
ex2_graph.add_edge("extract", "propose_work_order")
ex2_graph.add_edge("propose_work_order", "dispatch")
ex2_graph.add_edge("dispatch", END)
ex2_graph.add_edge("summarize", END)

checkpointer = MemorySaver()
ex2_app = ex2_graph.compile(checkpointer=checkpointer, interrupt_before=["dispatch"])

config = {"configurable": {"thread_id": "complaint-001"}}
init_state = {
    "complaint": test_complaints[0],
    "classification": "",
    "account_id": "",
    "summary": "",
    "proposed_work_order": "",
    "status": "",
}

paused = ex2_app.invoke(init_state, config)
print("PAUSED STATE:", paused["status"])
print("PROPOSED WORK ORDER:", paused["proposed_work_order"])

resumed = ex2_app.invoke(None, config)
print("RESUMED STATE:", resumed["status"])

# ============================================================
# EXERCISE 3: Retry Logic and Fallback Prompts
# ============================================================
print("\n" + "=" * 60)
print("EXERCISE 3: Retry Logic and Fallback Prompts")
print("=" * 60)

messy_complaints = [
    "my service acct is acting up again this is like the third time",
    "Ref: TCK-9042-B / urgent pls advise re: outage",
    "case ID acc-77401X keeps dropping connection every evening around 8pm",
    "internet has been flaky all week, nobody ever gave me a ticket number for it",
]


def is_valid_id(extracted_text):
    return bool(re.search(r"[A-Za-z0-9]*\d{2,}[A-Za-z0-9]*", extracted_text or ""))


def extract_with_retry(complaint, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        result = extract_chain.invoke({"complaint": complaint})
        if is_valid_id(result):
            return result
        time.sleep(2**attempt)
    return None


fallback_extract_prompt = ChatPromptTemplate.from_template(
    "Look carefully for an account or ticket identifier in this text, indicated by markers like "
    "'#', 'Ref:', 'Ticket', 'Account', 'ID', followed by alphanumeric characters. "
    "Return ONLY that identifier. If no such marker and identifier exist, return exactly: NOT_FOUND\n\n"
    "Text: {complaint}"
)
fallback_extract_chain = fallback_extract_prompt | model | StrOutputParser()


def extract_with_retry_and_fallback(complaint, max_attempts=3):
    result = extract_with_retry(complaint, max_attempts)
    if result is None:
        result = fallback_extract_chain.invoke({"complaint": complaint}).strip()
    return result


print("\nBEFORE (original chain, no retry/fallback):")
for c in messy_complaints:
    print(f"  {c!r} -> {extract_chain.invoke({'complaint': c})}")

print("\nAFTER (retry + fallback):")
for c in messy_complaints:
    print(f"  {c!r} -> {extract_with_retry_and_fallback(c)}")

print("\n" + "=" * 60)
print("PORTFOLIO COMPLETE")
print("=" * 60)
