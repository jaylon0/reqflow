"""OutputValidator -- code-level validation of Agent outputs."""

from __future__ import annotations

from pathlib import Path

from .models import (
    StageOutput,
    ValidationResult,
    ValidationIssue,
    AgentReport,
    StageAnalysis,
)


class OutputValidator:
    """Validate Agent outputs against stage requirements."""

    # stage_id -> required skills
    STAGE_REQUIRED_SKILLS: dict[str, list[str]] = {
        "PRD理解": ["prd-review"],
        "技术方案": ["tech-plan", "security-audit"],
        "代码审查": ["code-review", "security-audit"],
        "交付验证": ["delivery-check"],
        "总结": ["write-docs"],
    }

    # stages that require debate
    DEBATE_REQUIRED_STAGES: list[str] = [
        "PRD理解", "技术方案", "代码审查", "交付验证",
    ]

    def validate(self, stage_id: str, output: StageOutput) -> ValidationResult:
        """Validate stage output."""
        issues: list[ValidationIssue] = []

        # 1. Status check
        if output.status == "failed":
            return ValidationResult(passed=False, issues=[
                ValidationIssue("stage_failed", "阶段执行失败", severity="error")
            ])

        # 2. Analysis validation
        issues.extend(self._validate_analysis(output))

        # 3. Agent report validation
        issues.extend(self._validate_agent_reports(output))

        # 4. Debate validation (critical stages only)
        if stage_id in self.DEBATE_REQUIRED_STAGES:
            issues.extend(self._validate_debate(output))

        # 5. Skill validation
        issues.extend(self._validate_skills(stage_id, output))

        # 6. Artifact validation
        issues.extend(self._validate_artifacts(output))

        return ValidationResult(
            passed=not any(i.severity == "error" for i in issues),
            issues=issues,
        )

    def _validate_analysis(self, output: StageOutput) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not output.analysis or (not output.analysis.summary and not output.analysis.findings):
            issues.append(ValidationIssue("missing_analysis", "阶段缺少分析报告", severity="error"))
            return issues

        analysis = output.analysis

        # Length check
        if len(analysis.summary) < 100:
            issues.append(ValidationIssue(
                "analysis_too_short",
                f"分析不足 100 字（当前 {len(analysis.summary)}）",
                severity="error",
            ))

        # Specificity check
        if not self._has_concrete_references(analysis.summary):
            issues.append(ValidationIssue(
                "analysis_generic",
                "分析缺少具体引用（文件路径、代码、技术术语）",
                severity="warning",
            ))

        # Findings count
        if len(analysis.findings) < 3:
            issues.append(ValidationIssue(
                "findings_insufficient",
                f"发现不足 3 条（当前 {len(analysis.findings)}）",
                severity="error",
            ))

        return issues

    def _validate_agent_reports(self, output: StageOutput) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for report in output.agent_reports:
            if len(report.conclusion) < 50:
                issues.append(ValidationIssue(
                    "agent_conclusion_short",
                    f"{report.role} 结论不足 50 字（当前 {len(report.conclusion)}）",
                    severity="error",
                ))

            if not (0 <= report.confidence <= 1):
                issues.append(ValidationIssue(
                    "invalid_confidence",
                    f"{report.role} 置信度不在 0-1 范围",
                    severity="error",
                ))

        return issues

    def _validate_debate(self, output: StageOutput) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        if not output.debate_result:
            issues.append(ValidationIssue(
                "missing_debate",
                "关键阶段缺少辩论记录",
                severity="error",
            ))
            return issues

        debate = output.debate_result

        if len(debate.consensus) < 100:
            issues.append(ValidationIssue(
                "consensus_short",
                f"辩论共识不足 100 字（当前 {len(debate.consensus)}）",
                severity="error",
            ))

        if len(debate.rounds) < 2:
            issues.append(ValidationIssue(
                "debate_rounds_insufficient",
                f"辩论不足 2 轮（当前 {len(debate.rounds)}）",
                severity="error",
            ))

        if debate.convergence_score < 0.7:
            issues.append(ValidationIssue(
                "low_convergence",
                f"共识度过低：{debate.convergence_score}",
                severity="error",
            ))

        return issues

    def _validate_skills(self, stage_id: str, output: StageOutput) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        required = self.STAGE_REQUIRED_SKILLS.get(stage_id, [])
        for skill in required:
            if skill not in (output.skills_used or []):
                issues.append(ValidationIssue(
                    "missing_required_skill",
                    f"阶段未加载必需的 skill: {skill}",
                    severity="error",
                ))

        return issues

    def _validate_artifacts(self, output: StageOutput) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for artifact in output.artifacts:
            if artifact.type == "file" and artifact.path:
                p = Path(artifact.path)
                if not p.exists():
                    issues.append(ValidationIssue(
                        "missing_artifact",
                        f"产物文件不存在：{artifact.path}",
                        severity="error",
                    ))
                elif p.stat().st_size < 50:
                    issues.append(ValidationIssue(
                        "artifact_too_short",
                        f"产物内容过短：{artifact.path}",
                        severity="warning",
                    ))

        return issues

    @staticmethod
    def _has_concrete_references(text: str) -> bool:
        """Check whether text contains concrete references."""
        indicators = [
            "/" in text,
            any(ext in text for ext in [".py", ".java", ".ts", ".yaml", ".json"]),
            any(kw in text for kw in ["Controller", "Service", "Repository", "def ", "class "]),
            "```" in text,
        ]
        return sum(indicators) >= 2
