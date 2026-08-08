import time, re
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)

# ---- Exercise 1's extract chain ----
extract_prompt = ChatPromptTemplate.from_template(
    "Extract the account or ticket ID number from this complaint. "
    "Respond with only the ID (digits), nothing else.\n\nComplaint: {complaint}"
)
extract_chain = extract_prompt | model | StrOutputParser()

# ---- Task 1: messy inputs ----
messy_complaints = [
    "my service acct is acting up again this is like the third time",
    "Ref: TCK-9042-B / urgent pls advise re: outage",
    "case ID acc-77401X keeps dropping connection every evening around 8pm",
    "internet has been flaky all week, nobody ever gave me a ticket number for it",
]

print("--- Task 1: original chain on messy inputs ---")
for c in messy_complaints:
    print(c, "->", extract_chain.invoke({"complaint": c}))


# ---- Task 2: retry + validation ----
def is_valid_id(extracted_text):
    return bool(re.search(r"[A-Za-z0-9]*\d{2,}[A-Za-z0-9]*", extracted_text or ""))


def extract_with_retry(complaint, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        result = extract_chain.invoke({"complaint": complaint})
        if is_valid_id(result):
            return result
        print(f"Attempt {attempt} failed, retrying...")
        time.sleep(2**attempt)
    return None


print("\n--- Task 2: retry only ---")
for c in messy_complaints:
    print(extract_with_retry(c))

# ---- Task 3: fallback prompt ----
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


print("\nBEFORE (Task 1, original chain):")
for c in messy_complaints: 
    print(c, "->", extract_chain.invoke({"complaint": c}))

print("\nAFTER (retry + fallback):")
for c in messy_complaints:
    print(extract_with_retry_and_fallback(c))
