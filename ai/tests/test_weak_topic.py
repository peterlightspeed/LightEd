import pytest

from lighted_ai.weak_topics import (
    detect_weak_topics,
    weak_topic_names,
)


def test_groups_topic_names_case_insensitively():
    results = detect_weak_topics([
        {"topic": "VLAN", "score": 40},
        {"topic": " vlan ", "score": 60},
    ])

    assert len(results) == 1
    assert results[0].attempts == 2
    assert results[0].avg_score == 50.0
    assert results[0].status == "weak"


@pytest.mark.parametrize("score", [-1, 101, float("nan"), float("inf"), True])
def test_rejects_invalid_scores(score):
    with pytest.raises(ValueError):
        detect_weak_topics([{"topic": "VLAN", "score": score}])


def test_missing_score_is_not_silently_zero():
    with pytest.raises(ValueError):
        detect_weak_topics([{"topic": "VLAN"}])


def test_empty_attempts():
    assert detect_weak_topics([]) == []
    assert weak_topic_names([]) == []


def test_weak_topic_names_excludes_ok_and_strong():
    results = weak_topic_names([
        {"topic": "VLAN", "score": 30},
        {"topic": "Firewall", "score": 70},
        {"topic": "Encryption", "score": 90},
    ])

    assert results == ["VLAN"]