from lighted_ai.config import settings
from lighted_ai.embeddings import cosine_similarity, embed_text
from lighted_ai.performance import predict_performance
from lighted_ai.revision_planner import build_revision_plan
from lighted_ai.weak_topics import detect_weak_topics
from pytest import approx


def test_configured_embedding_shape(monkeypatch):
    class FakeGeminiClient:
        def embed(self, text, *, task_type, output_dimensionality):
            assert text == "derivatives and integrals"
            assert task_type == "RETRIEVAL_QUERY"
            assert output_dimensionality == 2
            return [3.0, 4.0]

    monkeypatch.setattr(settings, "embedding_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_embedding_dimensions", 2)
    v = embed_text(
        "derivatives and integrals",
        client=FakeGeminiClient(),
        task_type="RETRIEVAL_QUERY",
    )
    assert v == approx([0.6, 0.8], abs=1e-7)
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-5


def test_weak_topic_detection():
    attempts = [
        {"topic": "Algebra", "score": 30},
        {"topic": "Algebra", "score": 40},
        {"topic": "Geometry", "score": 90},
    ]
    topics = detect_weak_topics(attempts)
    assert topics[0].topic == "Algebra"
    assert topics[0].status == "critical"


def test_performance_prediction():
    pred = predict_performance([30, 40, 45])
    assert pred.label == "at_risk"
    assert 0 <= pred.pass_probability <= 1


def test_revision_plan():
    attempts = [{"topic": "Algebra", "score": 35}, {"topic": "Geometry", "score": 88}]
    plan = build_revision_plan(attempts)
    assert plan[0].topic == "Algebra"
    assert plan[0].priority == 1
