#


import anthropic
import json

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

test_notes = [
    "Pump 4 vibration levels remain within normal range after service.",
    "Conveyor belt 12 motor overheating, smoke smell reported, line stopped.",
    "Compressor unit 7 pressure gauge reading slightly inconsistent, monitoring.",
    "Emergency shutoff valve on Tank 3 failed to engage during test.",
    "Routine filter replacement completed on HVAC unit 2, no issues found.",
]

styles = {
    "1_zero_shot": "Classify the urgency of this maintenance note as LOW, MEDIUM, or HIGH: {note}",
    "2_role": """You are a plant safety coordinator.
    Getting urgency wrong could put workers at risk or waste emergency response resources.
    Classify the urgency of this maintenance note as LOW, MEDIUM, or HIGH: {note}""",
    "3_few_shot": """Classify maintenance notes as LOW, MEDIUM, or HIGH urgency.

Example 1:
Note: "Backup generator tested successfully, no faults found."
Urgency: LOW

Example 2:
Note: "Boiler pressure valve stuck, steam leaking near control panel, area evacuated."
Urgency: HIGH

Now classify this note:
{note}
Urgency:""",
    "4_cot": """Classify the urgency of this maintenance note as LOW, MEDIUM, or HIGH.
Think step by step:
1) What equipment/system is involved?
2) Is there an immediate safety risk?
3) What happens if this is ignored?
Then give your final answer as "Urgency: LOW/MEDIUM/HIGH".

Note: {note}""",
    "5_structured": """Classify the urgency of this maintenance note as LOW, MEDIUM, or HIGH.
Return ONLY valid JSON, no other text, in this exact format:
{{"urgency": "LOW|MEDIUM|HIGH", "reason": "one sentence explanation"}}

Note: {note}""",
}

results = []

for style_name, prompt_template in styles.items():
    for note in test_notes:
        prompt = prompt_template.format(note=note)
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        output_text = response.content[0].text.strip()
        results.append({"style": style_name, "note": note, "output": output_text})
        print(f"[{style_name}] {note[:40]}...")
        print(f"  -> {output_text}\n")

with open("exercise1_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Done. 25 results saved to exercise1_results.json")
