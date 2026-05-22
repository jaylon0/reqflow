from core.confidence import ConfidenceAssessor, ConfidenceLevel


def test_assess_high():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=1.0, consistency=1.0, accuracy=0.9,
        testability=0.7, risk_coverage=0.7, spec_compliance=0.8,
    )
    assert result.level == ConfidenceLevel.HIGH


def test_assess_medium():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=0.7, consistency=0.6, accuracy=0.8,
        testability=0.6, risk_coverage=0.6, spec_compliance=0.6,
    )
    assert result.level == ConfidenceLevel.MEDIUM


def test_assess_low():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=0.3, consistency=0.4, accuracy=0.3,
        testability=0.3, risk_coverage=0.3, spec_compliance=0.3,
    )
    assert result.level == ConfidenceLevel.LOW


def test_routing_high():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=1.0, consistency=1.0, accuracy=0.9,
        testability=0.7, risk_coverage=0.7, spec_compliance=0.8,
    )
    assert result.action == "proceed"


def test_routing_medium():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=0.7, consistency=0.6, accuracy=0.8,
        testability=0.6, risk_coverage=0.6, spec_compliance=0.6,
    )
    assert result.action == "pause"


def test_routing_low():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=0.3, consistency=0.4, accuracy=0.3,
        testability=0.3, risk_coverage=0.3, spec_compliance=0.3,
    )
    assert result.action == "retry"


def test_retry_escalation():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=0.3, consistency=0.4, accuracy=0.3,
        testability=0.3, risk_coverage=0.3, spec_compliance=0.3,
        retry_count=2,
    )
    assert result.action == "escalate"


def test_spec_compliance_dimension():
    assessor = ConfidenceAssessor()
    result = assessor.assess(
        completeness=0.9, consistency=0.9, accuracy=0.9,
        testability=0.9, risk_coverage=0.9, spec_compliance=0.9,
    )
    assert len(result.dimensions) == 6
    assert result.dimensions[5].name == "Spec合规"
