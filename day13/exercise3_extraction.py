import json
import re
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env

test_notes = [
    "On 03/14, Pump 4 began showing elevated vibration during the morning "
    "shift. Technician flagged for inspection within 48 hours -- not an "
    "immediate safety concern.",
    "URGENT -- Tank 3 emergency shutoff valve failed during routine test "
    "this morning. Line supervisor notified immediately.",
    "Filter replacement on HVAC unit 2 completed, no issues.",
    "Conveyor belt 12 motor showing signs of overheating, exact date of "
    "onset unclear, reported by night shift.",
    "Compressor unit 7 pressure readings inconsistent since last Tuesday, "
    "monitoring closely, no action taken yet.",
]

# ---------------------------------------------------------------
# Task 1: Baseline (deliberately loose, no schema, no examples)
# ---------------------------------------------------------------
baseline_prompt = """Extract the equipment_id, issue_type, severity, and
reported_date from this maintenance note: {note}"""

# ---------------------------------------------------------------
# Task 2: Improved (explicit schema + 2 few-shot examples)
# ---------------------------------------------------------------
improved_system = """Extract structured data from maintenance reports.
Return ONLY valid JSON matching this schema, no other text:
{
  "equipment_id": string,
  "issue_type": string,
  "severity": "low" | "medium" | "high",
  "reported_date": string | null,
  "requires_immediate_action": boolean
}
If a field cannot be determined from the text, use null.

Examples:

Note: "Generator 5 fuel line inspected 02/10, minor corrosion found, no
leak, scheduled for replacement next cycle."
Output: {"equipment_id": "Generator 5", "issue_type": "fuel line corrosion",
"severity": "low", "reported_date": "02/10", "requires_immediate_action": false}

Note: "Boiler 2 pressure relief valve stuck open, steam venting
continuously, area evacuated immediately."
Output: {"equipment_id": "Boiler 2", "issue_type": "pressure relief valve
stuck open", "severity": "high", "reported_date": null,
"requires_immediate_action": true}
"""


def call_claude(system, user_text):
    kwargs = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 300,
        "temperature": 0,
        "messages": [{"role": "user", "content": user_text}],
    }
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return resp.content[0].text.strip()


def run_baseline():
    results = []
    for note in test_notes:
        prompt = baseline_prompt.format(note=note)
        output = call_claude(system=None, user_text=prompt)
        results.append({"note": note, "output": output})
    return results


def run_improved():
    results = []
    for note in test_notes:
        output = call_claude(system=improved_system, user_text=f"Note: {note}")
        results.append({"note": note, "output": output})
    return results


# ---------------------------------------------------------------
# Task 3: Programmatic validation
# ---------------------------------------------------------------
REQUIRED_FIELDS = [
    "equipment_id",
    "issue_type",
    "severity",
    "reported_date",
    "requires_immediate_action",
]
VALID_SEVERITIES = {"low", "medium", "high"}


def _strip_code_fences(text):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return match.group(1) if match else text


def validate_extraction(raw_response):
    cleaned = _strip_code_fences(raw_response)
    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return (False, "invalid JSON: could not parse")

    if not isinstance(parsed, dict):
        return (False, "parsed JSON is not an object")

    missing = [f for f in REQUIRED_FIELDS if f not in parsed]
    if missing:
        return (False, f"missing fields: {missing}")

    if parsed["severity"] not in VALID_SEVERITIES:
        return (False, f"invalid severity value: {parsed['severity']!r}")

    return (True, parsed)


if __name__ == "__main__":
    print("Running baseline (Task 1)...")
    baseline_results = run_baseline()

    print("Running improved prompt (Task 2)...")
    improved_results = run_improved()

    print("\n=== BASELINE OUTPUTS ===")
    for r in baseline_results:
        print(f"Note: {r['note'][:50]}...\nOutput: {r['output']}\n")

    print("\n=== IMPROVED OUTPUTS ===")
    for r in improved_results:
        print(f"Note: {r['note'][:50]}...\nOutput: {r['output']}\n")

    baseline_pass = sum(
        1 for r in baseline_results if validate_extraction(r["output"])[0]
    )
    improved_pass = sum(
        1 for r in improved_results if validate_extraction(r["output"])[0]
    )

    print("\n=== VALIDATION RESULTS ===")
    for r in baseline_results:
        ok, info = validate_extraction(r["output"])
        print(f"[baseline] {'PASS' if ok else 'FAIL'} - {info if not ok else ''}")
    for r in improved_results:
        ok, info = validate_extraction(r["output"])
        print(f"[improved] {'PASS' if ok else 'FAIL'} - {info if not ok else ''}")

    print(f"\nBaseline (Task 1) success rate: {baseline_pass} / 5")
    print(f"Improved (Task 2) success rate: {improved_pass} / 5")
