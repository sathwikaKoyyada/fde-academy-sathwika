from langchain_anthropic import ChatAnthropic

base_model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

questions = [
    "How often should Pump 4 be inspected?",
    "What is the belt replacement schedule for conveyors?",
    "What is the warranty period for the HVAC system?",
]


base_answers = {}
for q in questions:
    response = base_model.invoke(q)
    base_answers[q] = response.content
    print(f"\nQ: {q}\nA: {response.content}")

print(
    "\n\nCopy these Base LLM answers, plus your Exercise 1 RAG answers, "
    "into the Task 2 comparison table in the exercise doc.\n"
    "Then classify each Base LLM answer for Task 3:\n"
    "  CORRECT_BY_COINCIDENCE / PLAUSIBLE_BUT_WRONG / APPROPRIATELY_UNCERTAIN"
)
