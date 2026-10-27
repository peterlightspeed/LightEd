"""AI helpers: quiz drafting + tutor answers.

Works in TWO modes so the product is useful with or without an API key:
  1. GEMINI_API_KEY set  -> Gemini writes the questions / answers (grounded in course text).
  2. No key              -> a transparent offline fallback (cloze-style questions built from the
                            lesson text; tutor answers = best matching lesson passages + sources).
The provider is hidden behind these functions so another LLM can replace Gemini later.
"""
import json
import logging
import random
import re

import httpx

from app.core.config import settings

logger = logging.getLogger("lighted.ai")

STOP = set(
    "the a an and or of to in on for with is are was were be been it its this that these those as at by from "
    "what why how when where which who whom do does did can could should would will you your i we they he she "
    "about into than then so if not no yes more most some any each other their there here have has had".split()
)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", text.lower())


# ------------------------------------------------------------------ Gemini
def _gemini(prompt: str, *, as_json: bool = False) -> str | None:
    if not settings.gemini_api_key:
        return None
    model = getattr(settings, "gemini_model", None) or "gemini-1.5-flash"
    body: dict = {"contents": [{"parts": [{"text": prompt}]}]}
    if as_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}
    try:
        res = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": settings.gemini_api_key},
            json=body,
            timeout=25,
        )
        res.raise_for_status()
        return res.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:  # noqa: BLE001 — any failure falls back to offline mode
        logger.warning("Gemini call failed; using offline fallback", exc_info=True)
        return None


# ------------------------------------------------------------------ quiz drafting
def validate_questions(raw) -> list[dict]:
    """Strict schema check (also used for teacher edits). Raises ValueError with a clear message."""
    if not isinstance(raw, list) or not (1 <= len(raw) <= 20):
        raise ValueError("A quiz needs between 1 and 20 questions")
    out = []
    for i, q in enumerate(raw, start=1):
        prompt = str(q.get("prompt", "")).strip()
        options = [str(o).strip() for o in q.get("options", []) if str(o).strip()]
        ans = q.get("answer_index")
        if not prompt:
            raise ValueError(f"Question {i} is empty")
        if not (2 <= len(options) <= 6):
            raise ValueError(f"Question {i} needs 2–6 options")
        if not isinstance(ans, int) or not (0 <= ans < len(options)):
            raise ValueError(f"Question {i} needs a correct answer selected")
        out.append({"prompt": prompt[:400], "options": [o[:200] for o in options], "answer_index": ans,
                    "explanation": str(q.get("explanation", "")).strip()[:400]})
    return out


def _offline_questions(title: str, content: str, n: int, distractor_pool: list[str]) -> list[dict]:
    """Cloze questions from the lesson text: blank out a key term, offer 3 distractors."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", content) if len(s.split()) >= 7]
    pool = list({w for w in _words(content) if w not in STOP and len(w) > 4} | set(distractor_pool))
    rng = random.Random(len(content))  # deterministic for the same lesson
    questions = []
    for s in sentences:
        cands = [w for w in _words(s) if w not in STOP and len(w) > 5]
        if not cands:
            continue
        answer = max(cands, key=len)
        others = [w for w in pool if w != answer]
        if len(others) < 3:
            continue
        opts = rng.sample(others, 3) + [answer]
        rng.shuffle(opts)
        blanked = re.sub(re.escape(answer), "_____", s, count=1, flags=re.I)
        questions.append({"prompt": f"Fill in the blank: {blanked}", "options": opts,
                          "answer_index": opts.index(answer), "explanation": f"From the lesson: “{s[:160]}”"})
        if len(questions) >= n:
            break
    if not questions:  # very short lesson: one generic comprehension question the teacher must edit
        questions.append({"prompt": f"Which statement best summarises “{title}”?",
                          "options": ["(edit option A)", "(edit option B)", "(edit option C)", "(edit option D)"],
                          "answer_index": 0, "explanation": "Edit this question before publishing."})
    return questions


def generate_questions(title: str, content: str, n: int, difficulty: str, distractor_pool: list[str]) -> tuple[list[dict], str]:
    """Returns (questions, provider). Teachers always review before publishing."""
    prompt = (
        f"You write quiz questions for a school course. Lesson title: {title}.\n"
        f"Difficulty: {difficulty}. Write {n} multiple-choice questions based ONLY on the lesson text below.\n"
        'Return ONLY JSON: a list of objects {"prompt": str, "options": [4 strings], "answer_index": 0-3, "explanation": str}.\n'
        f"LESSON TEXT:\n{content[:6000]}"
    )
    text = _gemini(prompt, as_json=True)
    if text:
        try:
            return validate_questions(json.loads(re.sub(r"^```json|```$", "", text.strip(), flags=re.M).strip())), "gemini"
        except Exception:  # noqa: BLE001
            logger.warning("Gemini returned invalid quiz JSON; using offline fallback")
    return _offline_questions(title, content, n, distractor_pool), "offline"


# ------------------------------------------------------------------ tutor
def tutor_answer(question: str, lessons: list[dict]) -> tuple[str, list[str], str]:
    """lessons = [{id,title,content,course}] the student may ask about. Returns (answer, sources, provider)."""
    q_terms = {w for w in _words(question) if w not in STOP}
    scored = []
    for l in lessons:
        text = f"{l['title']} {l['content']}"
        overlap = len(q_terms & set(_words(text)))
        if overlap:
            scored.append((overlap, l))
    scored.sort(key=lambda x: -x[0])
    top = [l for _, l in scored[:2]]
    sources = [f"{l['course']} › {l['title']}" for l in top]

    if not top:
        return (
            "I couldn't find that in your course material. Try using a key word from the lesson, "
            "or ask your teacher. (I only answer from your enrolled courses so I don't make things up.)",
            [],
            "offline",
        )

    context = "\n\n".join(f"[{l['title']}]\n{l['content'][:2500]}" for l in top)
    text = _gemini(
        "You are LightEd's friendly tutor. Answer the student's question using ONLY the course material below. "
        "Explain simply, give one short example, keep it under 150 words. If the material does not answer it, say so.\n\n"
        f"COURSE MATERIAL:\n{context}\n\nSTUDENT QUESTION: {question}"
    )
    if text:
        return text.strip(), sources, "gemini"

    # Offline: show the most relevant paragraphs from the lesson itself.
    paras = [p.strip() for l in top for p in re.split(r"\n\s*\n", l["content"]) if p.strip()]
    ranked = sorted(paras, key=lambda p: -len(q_terms & set(_words(p))))[:2]
    return ("Here's what your course material says:\n\n" + "\n\n".join(ranked), sources, "offline")
