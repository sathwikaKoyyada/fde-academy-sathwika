from langchain_core.prompts import ChatPromptTemplate
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env

# ---------------------------------------------------------------
# Template 1: Executive Summary Generator (worked example, given)
# ---------------------------------------------------------------
executive_summary_generator = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an operations analyst preparing a brief for a "
            "time-constrained executive. Write exactly 3 sentences: one on "
            "overall performance, one on the single biggest risk, one on "
            "a recommended next action. No jargon, no bullet points.",
        ),
        ("user", "Dashboard data: {dashboard_metrics}"),
    ]
)


# ---------------------------------------------------------------
# Template 2: Work Order Priority Classifier
# ---------------------------------------------------------------
work_order_priority_classifier = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a maintenance operations triage system feeding a Palantir "
            "Ontology Action. Classify the work order priority and return ONLY "
            "valid JSON in this exact schema, no other text:\n"
            '{{"priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL", '
            '"reason": string}}\n'
            "If a field cannot be determined, use null.",
        ),
        ("user", "Work order: {work_order_text}"),
    ]
)

# ---------------------------------------------------------------
# Template 3: Vehicle Issue Root Cause Classifier (capstone use case)
# ---------------------------------------------------------------
vehicle_issue_root_cause_classifier = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a senior automotive service diagnostician. Classify the "
            "issue into exactly one root-cause category: MECHANICAL, "
            "ELECTRICAL, SOFTWARE, COSMETIC, or UNKNOWN. Return ONLY JSON: "
            '{{"category": string, "confidence": "low"|"medium"|"high"}}\n\n'
            "Examples:\n"
            'Input: "Car won\'t start, dashboard lights flicker then die."\n'
            'Output: {{"category": "ELECTRICAL", "confidence": "high"}}\n\n'
            'Input: "Infotainment screen freezes randomly, needs restart."\n'
            'Output: {{"category": "SOFTWARE", "confidence": "high"}}',
        ),
        ("user", "Issue: {issue_text}"),
    ]
)

TEMPLATES = {
    "executive_summary_generator": executive_summary_generator,
    "work_order_priority_classifier": work_order_priority_classifier,
    "vehicle_issue_root_cause_classifier": vehicle_issue_root_cause_classifier,
}


def call_claude(messages, temperature=0):
    formatted = [{"role": r, "content": c} for r, c in messages]
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        temperature=temperature,
        messages=formatted,
    )
    return resp.content[0].text


def run_template(template, **params):
    messages = template.format_messages(**params)
    role_map = {"system": "user", "human": "user", "ai": "assistant"}
    # Claude API wants system separately; extract it
    system_text = None
    chat_msgs = []
    for m in messages:
        if m.type == "system":
            system_text = m.content
        else:
            chat_msgs.append({"role": "user", "content": m.content})
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        temperature=0,
        system=system_text,
        messages=chat_msgs,
    )
    return resp.content[0].text


if __name__ == "__main__":
    test_cases = {
        "executive_summary_generator": [
            {
                "dashboard_metrics": (
                    "On-time shipment rate: 91% (target 95%). "
                    "Average delivery delay: 1.8 days. "
                    "Warehouse capacity utilization: 88%. "
                    "Damaged goods rate: 2.1% (up from 1.4% last month). "
                    "Fleet fuel cost: $142,000 (3% under budget)."
                )
            },
        ],
        "work_order_priority_classifier": [
            {
                "work_order_text": "Forklift 12 hydraulic leak, minor, no production impact."
            },
            {
                "work_order_text": "Emergency stop button on Line 3 press unresponsive during safety check."
            },
        ],
        "vehicle_issue_root_cause_classifier": [
            {"issue_text": "Grinding noise from front brakes when stopping."},
            {
                "issue_text": "Paint peeling near left door handle, no functional impact."
            },
        ],
    }

    for name, cases in test_cases.items():
        print(f"\n=== {name} ===")
        for case in cases:
            output = run_template(TEMPLATES[name], **case)
            print(f"Input: {case}\nOutput: {output}\n")
