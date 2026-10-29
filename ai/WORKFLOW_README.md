# LightEd AI Workflow and Architecture Guide

This document maps the actual LightEd AI subsystem in the current `ai/ai` project folder. It explains the working architecture, data flow, and the purpose of each module in a way that is easy to understand for engineers, teammates, and future maintainers.

## 1. Purpose of this project

The AI folder is the learning intelligence layer for LightEd. It is responsible for:
- ingesting lesson materials from uploaded files
- splitting long content into useful chunks for context retrieval
- retrieving the most relevant course material for a question or topic
- generating grounded MCQ quizzes from lesson evidence
- validating quiz quality before exposing it to learners
- answering student questions with course-grounded explanations
- tracking weak topics and predicting likely student performance risk

This is intentionally separated from the backend and UI so the AI logic can be tested and evolved independently.

## 2. Design boundaries

The AI layer is kept isolated from the rest of the platform.

Current boundary:
- AI code: `ai/ai/lighted_ai/`
- backend: separate project folder
- frontend: separate project folder

This separation is deliberate. It allows:
- independent testing and iteration
- cleaner environment management
- cleaner provider configuration and model routing
- easier later integration into the app backend and UI

## 3. High-level architecture

The system follows a retrieval-first pattern.

```text
Uploaded lesson material
        |
        v
Ingestion pipeline
        |
        v
Parent/child chunking
        |
        v
Hybrid retrieval (BM25 + vector search)
        |
        v
Selected lesson evidence
        |
        v
Quiz generation / tutoring / revision analysis
        |
        v
Student-facing output
```

This means the model is not answering from memory alone. It is grounded in actual lesson content retrieved from the uploaded material.

## 4. Core workflow

### 4.1 Ingestion flow

```text
file upload
  -> format validation
  -> extract text
  -> normalize text
  -> split into semantic chunks
  -> attach metadata
  -> return ingested lesson document
```

The ingestion layer turns raw course files into structured lesson chunks that can be searched and reused.

### 4.2 Retrieval flow

```text
student question
  -> lexical search
  -> vector search
  -> merge with reciprocal-rank fusion
  -> return the best matching lesson chunks
```

This hybrid approach works better than a single method alone because:
- lexical search catches exact concept keywords
- vector search catches semantic similarity
- reciprocal-rank fusion combines the two without forcing incompatible score scales together

### 4.3 Quiz generation flow

```text
retrieved lesson chunk
  -> create multiple-choice questions
  -> validate structure
  -> verify content against lesson evidence
  -> reject unsupported or ambiguous results
  -> return verified quiz to students
```

This is intentionally strict. The system fails closed rather than exposing uncertain quiz questions.

### 4.4 Tutor flow

```text
student question
  -> retrieve relevant support context
  -> build compact prompt with lesson evidence
  -> answer using grounded context
  -> return a brief and readable explanation
```

### 4.5 Performance analytics flow

```text
student assessment history
  -> compute score trend and recent performance features
  -> load or train model
  -> estimate pass probability
  -> classify at-risk vs on-track learner
```

This is a separate classical ML layer that complements the AI tutoring and quiz generation features.

## 5. Folder structure

```text
ai/
└── ai/
    ├── .env
    ├── README.md
    ├── WORKFLOW_README.md
    ├── demo_workflow.py
    ├── pyproject.toml
    ├── requirements.txt
    ├── data/
    ├── lighted_ai/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── gemini_client.py
    │   ├── provider_router.py
    │   ├── embeddings.py
    │   ├── retrieval.py
    │   ├── quiz_generator.py
    │   ├── lesson_quiz_flow.py
    │   ├── tutor.py
    │   ├── weak_topics.py
    │   ├── performance.py
    │   ├── revision_planner.py
    │   └── ingestion/
    │       ├── __init__.py
    │       └── pipeline.py
    └── tests/
        ├── test_ai.py
        ├── test_embeddings_integration.py
        ├── test_ingestion_retrieval.py
        ├── test_lesson_quiz_flow.py
        ├── test_quiz_generator.py
        ├── test_retrieval.py
        ├── test_retrival_quiz.py
        └── test_tutor.py
```

## 6. Key modules and responsibilities

### `config.py`
Responsible for environment configuration and model settings.
- reads `.env` from the project folder
- resolves Gemini/Grok values
- sets embedding defaults and provider names
- prevents environment drift across shells and venvs

### `gemini_client.py`
Thin wrapper around Gemini generation and embedding calls.
- handles retries for temporary provider errors
- centralizes generation logic
- keeps provider-specific code away from the rest of the AI layer

### `provider_router.py`
Fallback provider manager.
- tries Gemini first
- falls back to Grok if Gemini is unavailable
- keeps a local fallback for demos and graceful degradation

### `embeddings.py`
Generates and validates vector embeddings.
- embed text for retrieval
- normalize vectors to support cosine-like similarity using dot products
- validate shape and consistency

### `retrieval.py`
Hybrid retrieval engine.
- stores documents and chunks
- indexes text with BM25
- indexes vectors with FAISS
- merges results using reciprocal-rank fusion
- returns relevant lesson evidence for a question

### `ingestion/pipeline.py`
Lesson ingestion and chunking engine.
- supports text and common educational file types
- extracts and normalizes content
- creates parent/child chunks for better retrieval
- preserves file metadata for traceability

### `lesson_quiz_flow.py`
The orchestration layer between retrieval and quiz generation.
- takes raw or ingested lesson material
- retrieves the best context for the learner query
- sends the lesson evidence into quiz generation
- returns the final student-safe quiz

### `quiz_generator.py`
The assessment engine.
- generates multiple-choice questions
- validates structure and answer schema
- verifies correctness against the lesson
- fails closed when evidence is not strong enough

### `tutor.py`
The learner tutoring interface.
- retrieves relevant course context
- creates a grounded answer prompt
- answers the learner using the retrieved course evidence
- falls back cleanly if the provider is unavailable

### `weak_topics.py`
Learner analytics for topic weakness.
- identifies weak learning areas from historical attempt data
- helps personalize revision or quiz focus

### `performance.py`
Performance prediction module.
- validates historical score sequences
- builds feature vectors for trend and recent performance
- loads or trains a logistic-regression model
- returns pass probability and at-risk status

### `revision_planner.py`
Revision prioritization.
- turns weak-topic insights into a study plan
- helps focus revision on the most urgent learner needs

## 7. End-to-end system behavior

The full AI flow is:

```text
Upload lesson material
  -> extract text
  -> chunk content
  -> store and index it
  -> ask a question or generate a quiz
  -> retrieve the best relevant lesson context
  -> answer or assess using that evidence
  -> return a grounded result to the learner
```

This is the basis of the educational AI experience in the LightEd project.

## 8. Runtime and environment considerations

Important operational lessons from this project:
- use a single active Python environment consistently
- load values from the project `.env` instead of different shells
- watch for provider quota exhaustion and model availability issues
- prefer graceful fallback behavior when providers fail

## 9. Quick start

```bash
cd ai/ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python demo_workflow.py
python demo_workflow.py --real
python -m pytest -q
```

Windows PowerShell:

```powershell
cd C:\Users\Faith Adekunle\Desktop\workshop\buildathon\ai\ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python demo_workflow.py
python demo_workflow.py --real
python -m pytest -q
```

## 10. Final status

The AI subsystem is now structured, testable, and ready for integration into the wider platform:
- retrieval works
- quiz generation is grounded and validated
- tutoring is context-aware
- provider fallback is implemented
- performance prediction is ready for real training data

The biggest remaining dependencies are external API availability and real student data, not core AI architecture quality.


```text
User query
  -> embed query
  -> compare with FAISS dense index
  -> compute BM25 lexical score
  -> fuse rankings with RRF
  -> return top lessons/chunks
```

This turns the user’s question into a ranked list of the most relevant lesson sections.

### Quiz generation workflow

```text
Retrieved lesson chunk
  -> generate question set
  -> validate structure
  -> verify each question against lesson evidence
  -> reject invalid/uncertain output
  -> return clean student-facing quiz
```

This ensures the quiz is not just plausible but grounded in the lesson material.

## 7. Real project workflow in one cycle

This is the workflow the project is presently designed to support:

```text
1. A teacher or system uploads class material
2. Ingestion extracts and normalizes the content
3. Semantic parent/child chunks are produced
4. Chunks are embedded and stored in the retrieval index
5. A learner asks a question or requests a quiz
6. Retrieval finds the best matching lesson chunk
7. The chunk is used as the evidence source for tutoring or assessment
8. The AI generates a grounded answer or quiz
9. Verification ensures the final output is safe and supported by the lesson
10. The backend/UI can later consume the final data
```

## 8. Real project behavior

The current system is deliberately structured around four essential principles:

1. Keep the AI subsystem isolated
2. Keep the core workflow retrieval-based
3. Keep generation grounded in lesson evidence
4. Fail closed when confidence is weak

This means the AI module is designed to be safe and reusable before it is connected to the rest of the app.

## 9. Example execution path

The project includes a direct demo entrypoint:

- `demo_workflow.py`

This script demonstrates the full end-to-end flow:

```bash
python demo_workflow.py
```

Its output includes:
- ingestion summary
- retrieved best match
- generated quiz questions and explanations

## 10. Data model summary

### `IngestedDocument`

Represents one source file after ingestion.

Fields:
- `source_name`
- `source_type`
- `content`
- `chunks`
- `metadata`

### `Chunk`

Represents a semantic chunk created from a document.

Fields:
- `chunk_id`
- `content`
- `chunk_level` (`parent` / `child`)
- `parent_chunk_id`
- `source_type`
- `location`
- `char_start`
- `char_end`

### `Document`

Used in retrieval indexing.

Fields:
- `id`
- `text`
- `metadata`

### `SearchResult`

Returned by the retriever.

Fields:
- `document`
- `score`

## 11. Reliability and safety rules

The system is intentionally conservative:

- no quiz is returned unless it passes structural validation
- no quiz is returned unless it passes semantic verification
- the quiz generator rejects ambiguous or unsupported questions
- retrieval does not force mismatched embedding models or inconsistent indices
- the AI logic stays separate from app integration so the safety boundaries stay clear

## 12. Current state of the project

As of the current implementation:

- the core AI architecture is working and validated
- ingestion, retrieval, and quiz generation are connected in practice
- the AI module is testable as a standalone subsystem
- backend and UI connection is still a future integration step
- live provider behavior depends on API key, external model availability, and network conditions

## 13. Recommended next integration step

When the rest of the team is ready, the clean integration path is:

```text
AI module API
  -> backend service layer
  -> UI / course manager
```

The backend should call the AI layer through a stable interface such as:

- ingest lesson file
- retrieve relevant context
- generate a quiz from a lesson
- ask a grounded question

This keeps the AI module modular and prevents UI/backend concerns from polluting the learning logic.

## 14. Practical usage examples

### Example 1: ingest and index a lesson file

```python
from lighted_ai.ingestion.pipeline import ingest_file
from lighted_ai.retrieval import Retriever

content = b"A VLAN separates devices into logical network segments."
ingested = ingest_file(content, "lesson.txt")
retriever = Retriever()
retriever.add_ingested_documents([ingested])
```

### Example 2: retrieve the best lesson chunk for a query

```python
results = retriever.search("How do VLANs separate devices?", top_k=1)
print(results[0].document.text)
```

### Example 3: generate a quiz from a retrieved lesson

```python
from lighted_ai.lesson_quiz_flow import generate_quiz_from_lesson

quiz = generate_quiz_from_lesson(
    lesson=ingested,
    query="How do VLANs separate devices?",
    num_questions=2,
)
print(quiz)
```

## 15. Summary

The current AI subsystem is a clean and practical architecture for educational material processing and student-facing assessment generation.

It includes:
- file ingestion
- semantic chunking
- retrieval
- grounded quiz generation
- verification and fail-safe logic

The system is ready as an isolated AI service layer and is prepared for the later backend/UI handoff without coupling the application logic to the AI internals.
