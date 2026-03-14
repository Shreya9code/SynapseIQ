from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset

data = {
    "question": [
        "What is the main topic of the document?"
    ],
    "answer": [
        "The paper discusses AI research."
    ],
    "contexts": [
        ["AI research explores machine learning methods..."]
    ],
}

dataset = Dataset.from_dict(data)

result = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision
    ],
)

print(result)