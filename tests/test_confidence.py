from core.confidence import ConfidenceAssessor, ConfidenceLevel


def test_assess_high():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=1.0, consistency=1.0, accuracy=0.9)
    assert result.level == ConfidenceLevel.HIGH


def test_assess_medium():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=0.7, consistency=0.6, accuracy=0.8)
    assert result.level == ConfidenceLevel.MEDIUM


def test_assess_low():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=0.3, consistency=0.4, accuracy=0.2)
    assert result.level == ConfidenceLevel.LOW


def test_routing_high():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=1.0, consistency=1.0, accuracy=0.9)
    assert result.action == "proceed"


def test_routing_medium():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=0.7, consistency=0.6, accuracy=0.8)
    assert result.action == "pause"


def test_routing_low():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=0.3, consistency=0.4, accuracy=0.2)
    assert result.action == "retry"


def test_retry_escalation():
    assessor = ConfidenceAssessor()
    result = assessor.assess(completeness=0.3, consistency=0.4, accuracy=0.2, retry_count=2)
    assert result.action == "escalate"
