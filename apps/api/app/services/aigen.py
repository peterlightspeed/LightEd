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
import time

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
# Google retires models regularly (gemini-1.5-* and 2.0-* now return 404). We therefore try the
# configured model first, then a short list of known-good fallbacks, and remember the first one
# that works so later requests don't repeat the 404s.
FALLBACK_MODELS = ("gemini-3.8-flash", "gemini-3.6-flash")
_working_model: str | None = None
_last_error: str | None = None


def _model_chain() -> list[str]:
    chain: list[str] = []
    for m in (_working_model, getattr(settings, "gemini_model", None), *FALLBACK_MODELS):
        m = (m or "").strip().removeprefix("models/")
        if m and m not in chain:
            chain.append(m)
    return chain


def _gemini_call(prompt: str, *, as_json: bool = False) -> tuple[str | None, str | None]:
    """Returns (text, error). Never raises. The API key travels in a header, never in the URL,
    so it cannot leak into httpx / server logs."""
    global _working_model, _last_error
    if not settings.gemini_api_key:
        return None, "GEMINI_API_KEY is not set on the server"

    body: dict = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    if as_json:
        body["generationConfig"] = {"responseMimeType": "application/json"}

    error = "unknown error"
    for model in _model_chain():
        for attempt in (1, 2):  # one quick retry for rate-limit / overload blips
            try:
                res = httpx.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": settings.gemini_api_key.strip(), "Content-Type": "application/json"},
                    json=body,
                    timeout=30,
                )
            except httpx.HTTPError as exc:
                error = f"network error talking to Gemini ({type(exc).__name__})"
                logger.warning("Gemini network error on %s: %s", model, type(exc).__name__)
                break  # no point trying other models if the network is down
            if res.status_code in (429, 500, 503) and attempt == 1:
                time.sleep(1.5)
                continue
            if res.status_code == 404:
                error = f"model '{model}' not found (retired or misspelt)"
                logger.warning("Gemini model %s returned 404; trying next fallback", model)
                break  # try the next model in the chain
            if res.status_code in (400, 401, 403):
                detail = ""
                try:
                    detail = res.json().get("error", {}).get("message", "")
                except Exception:  # noqa: BLE001
                    pass
                error = f"Gemini rejected the request ({res.status_code}): {detail[:160] or 'check GEMINI_API_KEY'}"
                logger.warning("Gemini %s on %s: %s", res.status_code, model, detail[:300])
                _last_error = error
                return None, error  # a bad key / bad request will fail on every model
            if not res.is_success:
                error = f"Gemini error {res.status_code}"
                logger.warning("Gemini HTTP %s on %s: %s", res.status_code, model, res.text[:300])
                break
            try:
                data = res.json()
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            except (KeyError, IndexError, TypeError, ValueError):
                reason = (res.json().get("promptFeedback") or {}).get("blockReason") if res.content else None
                error = f"Gemini returned no answer{f' (blocked: {reason})' if reason else ''}"
                logger.warning("Gemini empty/blocked response on %s: %s", model, res.text[:300])
                break
            if text:
                _working_model, _last_error = model, None
                return text, None
            error = "Gemini returned an empty answer"
            break
    _last_error = error
    return None, error


def _gemini(prompt: str, *, as_json: bool = False) -> str | None:
    text, _ = _gemini_call(prompt, as_json=as_json)
    return text


def gemini_status() -> dict:
    """Cheap live probe used by GET /ai/status so 'is the AI actually working?' is one request."""
    configured = bool(settings.gemini_api_key)
    out = {"configured": configured, "model": None, "ok": False, "error": None}
    if not configured:
        out["error"] = "GEMINI_API_KEY is not set on the server"
        return out
    text, err = _gemini_call("Reply with the single word: ok")
    out.update(ok=bool(text), model=_working_model if text else (_model_chain() or [None])[0], error=err)
    return out


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
# Words that describe HOW to answer, not WHAT the topic is. "Explain this in simple words" has no
# topic of its own, so it must lean on the previous question instead of failing to match.
GENERIC = set(
    "explain simple simply words word example examples give tell focus first help please understand "
    "meaning mean means again more detail details summary summarise summarize short shorter easy easier "
    "step steps show much many better best start idea topic lesson lessons course courses thing things know "
    "learn about like using just really make sure quick quickly basic basics overview".split()
)


def _stem(w: str) -> str:
    """Very small stemmer so 'accelerating' / 'accelerations' still match 'acceleration'."""
    if w.endswith(("ss", "us", "is")):  # focus, class, analysis: the final s is part of the word
        return w
    for suf in ("ations", "ation", "ingly", "ing", "ies", "ied", "ers", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def _terms(text: str) -> set[str]:
    return {_stem(w) for w in _words(text) if w not in STOP}


def _topic_terms(text: str) -> set[str]:
    """Stems of the words that name an actual topic (filler like 'explain'/'example' removed first)."""
    return {_stem(w) for w in _words(text) if w not in STOP and w not in GENERIC and _stem(w) not in GENERIC}


def tutor_answer(
    question: str, lessons: list[dict], history: list[dict] | None = None
) -> tuple[str, list[str], str, str | None]:
    """lessons = [{id,title,content,course}] the student may ask about.
    history = [{"role": "user"|"tutor", "text": str}] (most recent last, optional).
    Returns (answer, sources, provider, notice). `notice` explains when the AI model was NOT used."""
    history = [h for h in (history or []) if isinstance(h, dict) and str(h.get("text", "")).strip()][-6:]
    prior_questions = [str(h["text"]) for h in history if h.get("role") == "user"]

    q_terms = _topic_terms(question)
    follow_up = False
    if not q_terms and prior_questions:  # "give me an example" -> reuse what we were just talking about
        q_terms = _topic_terms(prior_questions[-1])
        follow_up = True

    scored = []
    for l in lessons:
        title_terms, body_terms = _terms(l["title"]), _terms(l["content"])
        overlap = len(q_terms & body_terms) + 2 * len(q_terms & title_terms)  # title hits count double
        if overlap:
            scored.append((overlap, l))
    scored.sort(key=lambda x: -x[0])
    # Keep a second lesson only if it is nearly as relevant as the best one (avoids incidental one-word matches).
    top = [l for sc, l in scored[:2] if sc >= scored[0][0] * 0.6] if scored else []

    overview = False
    if not top and not _topic_terms(question) and not follow_up and lessons:
        # Pure "how should I study?" style question: point at the start of the student's courses.
        top, overview = lessons[:2], True

    sources = [f"{l['course']} › {l['title']}" for l in top]
    if not top:
        return (
            "I couldn't find that in your course material. Try using a key word from the lesson, "
            "or ask your teacher. (I only answer from your enrolled courses so I don't make things up.)",
            [],
            "offline",
            None,
        )

    context = "\n\n".join(f"[{l['title']}]\n{l['content'][:2500]}" for l in top)
    outline = ""
    if overview:
        outline = "\nOther lessons in the student's courses: " + ", ".join(l["title"] for l in lessons[:12]) + "\n"
    convo = ""
    if history:
        convo = "\nCONVERSATION SO FAR:\n" + "\n".join(
            f"{'Student' if h.get('role') == 'user' else 'Tutor'}: {str(h['text'])[:400]}" for h in history
        ) + "\n"

    text, err = _gemini_call(
        "You are LightEd's friendly tutor. Answer the student's question using ONLY the course material below. "
        "Explain simply, give one short example, keep it under 150 words. If the material does not answer it, say so.\n\n"
        f"COURSE MATERIAL:\n{context}\n{outline}{convo}\nSTUDENT QUESTION: {question}"
    )
    if text:
        return text.strip(), sources, "gemini", None

    # Offline: show the most relevant paragraphs from the lesson itself.
    paras = [p.strip() for l in top for p in re.split(r"\n\s*\n", l["content"]) if p.strip()]
    ranked = sorted(paras, key=lambda p: -len(q_terms & _terms(p)))[:2]
    notice = "The AI model is unavailable right now, so I'm showing the closest passages from your lesson instead."
    logger.warning("Tutor fell back to offline mode: %s", err)
    return ("Here's what your course material says:\n\n" + "\n\n".join(ranked), sources, "offline", notice)
