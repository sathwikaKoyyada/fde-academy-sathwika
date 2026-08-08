from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from typing import TypedDict

model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

test_complaints = [
    "Account #48213 - My internet has been down for 6 hours and I work from home. This is costing me money. Fix this NOW.",
    "Ticket #9042 - Billing seems slightly higher this month than usual, could someone check when convenient? No rush.",
    "Account #77410 - Complete outage across my whole building, multiple neighbors affected, please escalate immediately.",
    "Just wanted to say the new app update looks nice. Ticket #201.",
]

# ---- Task 1: chains ----
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

classify_chain = classify_prompt | model | StrOutputParser()
extract_chain = extract_prompt | model | StrOutputParser()
summarize_chain = summarize_prompt | model | StrOutputParser()

print("--- Task 1: classify test ---")
for c in test_complaints:
    print(classify_chain.invoke({"complaint": c}))


# ---- Task 2: graph ----
class ComplaintState(TypedDict):
    complaint: str
    classification: str
    account_id: str
    summary: str


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


def route_after_classify(state):
    return "extract" if state["classification"] == "URGENT" else "summarize"


graph = StateGraph(ComplaintState)
graph.add_node("classify", classify_node)
graph.add_node("extract", extract_node)
graph.add_node("summarize", summarize_node)
graph.set_entry_point("classify")
graph.add_conditional_edges(
    "classify", route_after_classify, {"extract": "extract", "summarize": "summarize"}
)
graph.add_edge("extract", END)
graph.add_edge("summarize", END)
app = graph.compile()

# ---- Task 3: run all 4 ----
print("\n--- Task 3: full runs ---")
for complaint in test_complaints:
    result = app.invoke(
        {"complaint": complaint, "classification": "", "account_id": "", "summary": ""}
    )
    print(result)
