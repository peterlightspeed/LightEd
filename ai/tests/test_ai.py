from lighted_ai.embeddings import cosine_similarity, embed_text
from lighted_ai.performance import predict_performance
from lighted_ai.revision_planner import build_revision_plan
from lighted_ai.weak_topics import detect_weak_topics


def test_hash_embedding_shape():
    v = embed_text("derivatives and integrals")
    assert len(v) > 0
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
