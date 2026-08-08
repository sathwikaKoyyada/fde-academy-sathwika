from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

vectorstore = Chroma(
    collection_name="operations_manual",
    embedding_function=HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ),
    persist_directory="./chroma_db",
)

stored = vectorstore.get()
print("Stored chunk ids:", stored["ids"])

test_set = [
    {
        "question": "How often should Pump 4 be inspected?",
        "relevant_chunk_ids": {"4.2_0"},
    },
    {
        "question": "What triggers an immediate pump inspection regardless of schedule?",
        "relevant_chunk_ids": {"4.2_0"},
    },
    {
        "question": "How often are conveyor belts visually inspected?",
        "relevant_chunk_ids": {"4.5_0"},
    },
    {
        "question": "What happens if an emergency shutoff valve fails its monthly test?",
        "relevant_chunk_ids": {"6.1_0"},
    },
    {
        "question": "How long does a facility have to replace a failed emergency shutoff valve?",
        "relevant_chunk_ids": {"6.1_0"},
    },
]


def evaluate_retrieval(test_set, vectorstore, k=3):
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    results = []
    for item in test_set:
        retrieved_docs = retriever.invoke(item["question"])
        retrieved_ids = set()
        for d in retrieved_docs:
            match = vectorstore.get(where={"section": d.metadata["section"]})
            for cid, doc in zip(match["ids"], match["documents"]):
                if doc == d.page_content:
                    retrieved_ids.add(cid)

        relevant = item["relevant_chunk_ids"]
        true_positives = retrieved_ids & relevant
        precision = len(true_positives) / len(retrieved_ids) if retrieved_ids else 0
        recall = len(true_positives) / len(relevant) if relevant else 0

        results.append(
            {
                "question": item["question"],
                "retrieved_ids": retrieved_ids,
                "precision": precision,
                "recall": recall,
            }
        )
    return results


results = evaluate_retrieval(test_set, vectorstore, k=3)
for r in results:
    print(r)

avg_precision = sum(r["precision"] for r in results) / len(results)
avg_recall = sum(r["recall"] for r in results) / len(results)
print(f"\nAverage precision: {avg_precision:.2f}  Average recall: {avg_recall:.2f}")

print("\nTo tune: re-run with k=1:")
results_k1 = evaluate_retrieval(test_set, vectorstore, k=1)
avg_precision_k1 = sum(r["precision"] for r in results_k1) / len(results_k1)
avg_recall_k1 = sum(r["recall"] for r in results_k1) / len(results_k1)
print(
    f"k=1 -> Average precision: {avg_precision_k1:.2f}  Average recall: {avg_recall_k1:.2f}"
)
