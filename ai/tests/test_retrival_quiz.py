from lighted_ai.quiz_generator import generate_quiz
from lighted_ai.retrieval import Document, Retriever


def build_retriever() -> Retriever:
    documents = [
        Document(
            "vlan",
            "A VLAN separates devices into logical network segments.",
        ),
        Document(
            "firewall",
            "A firewall allows or blocks incoming and outgoing network traffic using security rules.",
        ),
        Document(
            "subnet_mask",
            "A subnet mask identifies which part of an IP address belongs to the network and which part identifies a host.",
        ),
        Document(
            "encryption",
            "Encryption protects information by transforming it into unreadable data that requires the correct key to decode.",
        ),
    ]

    retriever = Retriever()
    retriever.add_documents(documents)
    return retriever


def main() -> None:
    retriever = build_retriever()
    queries = [
        "How can I put groups of devices on separate logical networks without changing physical cabling?",
        "What controls whether incoming or outgoing traffic is allowed based on security rules?",
        "How do I tell which portion of an IP address identifies the network versus a host?",
        "How can I keep information unreadable to someone who does not have the right key?",
    ]

    for query in queries:
        result = retriever.search(query, top_k=1)[0]
        lesson_text = result.document.text
        title = result.document.metadata.get("title") or result.document.id

        print(f"\nQuery: {query}")
        print(f"Best match: {lesson_text}")
        quiz = generate_quiz(
            lesson_content=lesson_text,
            num_questions=2,
            title=title,
            topic_focus=title,
        )
        for index, item in enumerate(quiz, start=1):
            print(f"  Q{index}: {item['question']}")
            for option_index, option in enumerate(item['options']):
                marker = "*" if option_index == item["answer_index"] else " "
                print(f"    {marker} {option_index}: {option}")
            print(f"    explanation: {item['explanation']}")


if __name__ == "__main__":
    main()
