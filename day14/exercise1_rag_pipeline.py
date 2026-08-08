from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

SECTIONS = [
    {
        "section": "4.2",
        "text": (
            "Section 4.2 - Pump Maintenance: Pump 4 requires inspection every "
            "90 days under normal operating conditions. If ambient temperature "
            "exceeds 40C, reduce the interval to 60 days. Vibration readings "
            "above 8mm/s require immediate inspection regardless of schedule."
        ),
    },
    {
        "section": "4.5",
        "text": (
            "Section 4.5 - Conveyor Systems: Conveyor belts should be visually "
            "inspected weekly for wear. Full belt replacement is recommended "
            "after 18 months of continuous operation or at the first sign of "
            "fraying, whichever comes first."
        ),
    },
    {
        "section": "6.1",
        "text": (
            "Section 6.1 - Emergency Shutoff: All emergency shutoff valves "
            "must be tested monthly. A failed test requires the valve to be "
            "tagged out of service and replaced within 24 hours."
        ),
    },
]

splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=40)

ids, docs, metadatas = [], [], []
for sec in SECTIONS:
    chunks = splitter.split_text(sec["text"])
    for i, chunk in enumerate(chunks):
        ids.append(f"{sec['section']}_{i}")
        docs.append(chunk)
        metadatas.append({"section": sec["section"]})

vectorstore = Chroma(
    collection_name="operations_manual",
    embedding_function=HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ),
    persist_directory="./chroma_db",
)

existing = vectorstore.get()["ids"]
if existing:
    vectorstore.delete(ids=existing)

vectorstore.add_texts(texts=docs, ids=ids, metadatas=metadatas)
print(f"Indexed {len(ids)} chunks into 'operations_manual': {ids}")

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

prompt = ChatPromptTemplate.from_template(
    "You are an operations-manual assistant. Answer ONLY using the context below. "
    "If the answer is not present in the context, explicitly say the manual does "
    "not cover this topic. Do not guess or use outside knowledge.\n\n"
    "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
)

model = ChatAnthropic(model="claude-sonnet-4-6", temperature=0)
parser = StrOutputParser()


def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | parser
)

questions = [
    "How often should Pump 4 be inspected?",
    "What is the belt replacement schedule for conveyors?",
    "What is the warranty period for the HVAC system?",
]

print("\n=== Task 2: RAG Answers ===")
for q in questions:
    answer = rag_chain.invoke(q)
print(f"\nQ: {q}\nA: {answer}")

print("\n=== Task 3: Answers with Section Citations ===")
for q in questions:
    retrieved = retriever.invoke(q)
    sections_hit = [d.metadata["section"] for d in retrieved]
    answer = rag_chain.invoke(q)
    print(f"\nQ: {q}\nA: {answer}\nCited sections: {sections_hit}")
