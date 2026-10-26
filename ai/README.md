# LightEd AI Module

Pure-Python AI/ML layer. Importable as a library by the backend, and runnable as
a standalone worker/service. **No model is trained from scratch** — we use the
Gemini API for generation and lightweight classical ML for analytics.

## Responsibilities

| Module                | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `gemini_client.py`    | Thin wrapper around the Gemini API                   |
| `embeddings.py`       | Text → vector embeddings (Gemini `text-embedding-004`) |
| `retrieval.py`        | In-memory FAISS index over course material (RAG)     |
| `tutor.py`            | Grounded Q&A (retrieve → prompt → answer)            |
| `quiz_generator.py`   | Generate quiz questions from a lesson                |
| `weak_topics.py`      | Detect weak topics from attempt history              |
| `performance.py`      | Basic score prediction (logistic regression)         |
| `revision_planner.py` | Build a prioritized revision schedule                |

## Usage

```python
from lighted_ai.tutor import answer_question
from lighted_ai.weak_topics import detect_weak_topics

print(answer_question("What is a derivative?", course_id=1))
print(detect_weak_topics(attempts=[{"topic": "Algebra", "score": 40}]))
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=your-key
pytest
```
