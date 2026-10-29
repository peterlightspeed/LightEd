# LightEd AI Module

This folder contains the AI intelligence layer for the LightEd learning platform. It is intentionally isolated from the backend and UI so the model, retrieval, and assessment logic can be built, tested, and validated independently before integration.

The AI module is responsible for:
- ingesting and cleaning lesson materials
- chunking content into parent/child blocks for better retrieval
- retrieving the most relevant material for a learner question or lesson topic
- generating grounded quiz questions from lesson evidence
- verifying quiz correctness before exposing it to the learner
- tutoring a learner with context-based answers
- predicting risk of underperformance from historical scores

This is not a full-stack app. It is the AI backend layer for a learning system designed to eventually connect with the main backend and front-end services.

## 1. Project boundary

The current development boundary is:
- AI folder: `ai/ai/`
- backend: separate project folder
- frontend/UI: separate project folder

This AI layer is intentionally self-contained and exposed as a Python package named `lighted_ai`.

## 2. Architecture summary

The system follows a retrieval-first architecture:

```text
uploaded lesson file
        |
        v
ingestion + text extraction
        |
        v
parent/child chunking
        |
        v
hybrid retrieval (BM25 + FAISS)
        |
        v
selected lesson context
        |
        v
quiz generation / tutor response
        |
        v
student-facing output
```

The design separates concerns into clear modules:
- ingestion handles content extraction and chunking
- retrieval handles ranking and relevant content lookup
- generation handles quiz and answer creation
- verification ensures content is grounded in the lesson and valid
- performance analytics predicts learner risk from past scores

## 3. Why this architecture

The project uses this pattern because it is robust, explainable, and practical for educational AI:
- retrieval keeps answers grounded in lesson material instead of guessing from general model knowledge
- verification reduces hallucination risk and improves trust
- hybrid search gives better relevance than pure lexical or pure dense search alone
- student-facing output is sanitized so internal model reasoning is not shown to learners

## 4. Folder structure

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

## 5. Core modules

### 5.1 `config.py`

Handles environment and AI configuration.

Responsibilities:
- loads variables from the project `.env`
- resolves Gemini and Grok keys
- sets embedding provider and model defaults
- centralizes runtime configuration for the AI layer

This matters because the app previously ran into environment mismatch issues when different virtual environments were active.

### 5.2 `gemini_client.py`

A thin wrapper around the Gemini API.

Responsibilities:
- text generation
- embeddings
- retry logic for transient provider failures
- safer handling of safety-blocked or empty responses

### 5.3 `provider_router.py`

This is the provider fallback layer.

Responsibilities:
- try Gemini first
- fall back to Grok/XAI if Gemini is unavailable or quota-limited
- retain a local demo fallback for presentations and offline validation

This is important because real provider systems can fail from quota exhaustion, timeout, or model unavailability even when the app code itself is fine.

### 5.4 `embeddings.py`

Generates and validates embeddings used by retrieval.

Responsibilities:
- embed lesson chunks and queries
- normalize vectors
- prevent invalid vector shapes
- keep retrieval consistent across the index

### 5.5 `retrieval.py`

This is the hybrid retrieval system.

Responsibilities:
- store lesson documents and chunks
- build a BM25 lexical index
- create a FAISS vector index
- combine matching signals using reciprocal-rank fusion (RRF)
- return the most relevant evidence for a question or topic

This sits at the center of the learning assistant workflow because it provides the lesson-grounded evidence for both tutoring and quiz generation.

### 5.6 `ingestion/pipeline.py`

This handles lesson ingestion.

Responsibilities:
- validate uploaded file types
- extract text from content sources
- normalize text and metadata
- segment long material into parent and child chunks
- expose structured ingested lesson documents to the retriever

### 5.7 `lesson_quiz_flow.py`

This connects the whole flow together from lesson text to final quiz output.

Responsibilities:
- accept an ingested lesson or raw text
- retrieve the best matching chunk for the query
- pass the retrieved material to the quiz generator
- return student-safe quiz output

### 5.8 `quiz_generator.py`

This is the core assessment-generation engine.

Responsibilities:
- generate multiple-choice questions from lesson content
- validate JSON structure and answer schema
- verify each question against the lesson text
- reject invalid, ambiguous, or unsupported questions
- return only fully verified questions

This is the main component responsible for trustworthiness in the quiz layer.

### 5.9 `tutor.py`

Provides grounded Q&A for learners.

Responsibilities:
- retrieve relevant supporting context
- build a compact prompt from that context
- ask the provider for a concise answer
- fall back gracefully when the AI provider is unavailable

### 5.10 `weak_topics.py`

Examines learner performance histories and identifies weak learning areas.

Responsibilities:
- analyze attempt scores by subject/topic
- flag topics that have low performance
- support adaptive revision planning

### 5.11 `performance.py`

This module estimates whether a learner is likely to pass their next assessment based on historical score trends.

Responsibilities:
- validate score sequences
- build stable features from past attempt data
- train or load a logistic-regression model
- output risk labels and pass probabilities
- provide a reusable prediction API for dashboards or learner analytics

This is a classical ML component, separate from the LLM layer. It is useful for analytics and support decisions, but it does not replace the retrieval/generation AI pipeline.

### 5.12 `revision_planner.py`

Builds a prioritized revision plan from weak-topic and performance signals.

Responsibilities:
- rank topics by urgency
- create a study plan based on student performance
- connect learner analytics to targeted revision advice

## 6. End-to-end workflow

### 6.1 Ingestion

```text
Uploaded file
  -> validate supported file types
  -> extract text
  -> normalize content
  -> create parent/child chunks
  -> attach metadata and source information
  -> return ingested lesson object
```

### 6.2 Retrieval

```text
Student question or learning topic
  -> run BM25 lexical search
  -> run dense vector search
  -> combine results with RRF
  -> return top relevant lesson chunks
```

### 6.3 Quiz generation

```text
Relevant lesson chunk
  -> generate multiple-choice questions
  -> validate structure
  -> verify answer correctness against lesson evidence
  -> reject uncertain or unsupported output
  -> return student-safe verified quiz
```

### 6.4 Tutor response

```text
Student question
  -> retrieve relevant context
  -> compose grounded prompt
  -> call provider or fallback client
  -> return concise answer with cited source material
```

### 6.5 Performance analytics

```text
Historical assessment scores
  -> derive trend and performance features
  -> load or train prediction model
  -> estimate pass probability
  -> return risk classification
```

## 7. Runtime and environment notes

This project has historically had problems caused by multiple virtual environments and mismatched runtime configuration.

Important guidance:
- make sure the active Python runtime is the correct project environment
- ensure `.env` values are loaded from the AI project folder
- avoid mixing values from different venvs or shell sessions
- provider quota and model availability can fail even when the code is correct

A typical local setup looks like:

```bash
cd ai/ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python demo_workflow.py --real
```

On Windows PowerShell, similar commands are:

```powershell
cd C:\Users\Faith Adekunle\Desktop\workshop\buildathon\ai\ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python demo_workflow.py --real
```

## 8. Current project status

As of this project stage:
- the AI subsystem is structurally complete and isolated
- retrieval, quiz generation, and tutor logic work in the project runtime
- the provider fallback system is in place
- the final live system depends on valid external API keys and provider availability
- the performance module is implemented and ready for real training data

The main remaining operational risk is external: API keys, provider quota, and provider uptime. The application logic itself is stable and demo-ready in fallback mode.

## 9. Quick-start commands

```bash
cd ai/ai
python -m pytest -q
python demo_workflow.py
python demo_workflow.py --real
```

## 10. Recommended next steps

1. Validate the active Python environment is the intended one.
2. Use a valid Gemini or Grok key for live provider checks.
3. Train the performance model on real student assessment histories.
4. Connect the AI package to the backend endpoints once they are ready.
5. Keep the local deterministic demo client as a safe fallback for presentation mode.

This AI folder is the core intelligence layer for the platform and is already designed to scale into a production-ready learning assistant once the backend and UI are connected.

