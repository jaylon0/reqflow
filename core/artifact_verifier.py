"""Artifact Verifier — file existence and integrity verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ArtifactClaim:
    """A claimed file change."""
    path: str
    action: str  # "create" | "modify"


@dataclass
class ArtifactDetail:
    """Verification result for a single artifact."""
    path: str
    action: str
    exists: bool
    passed: bool
    message: str = ""


@dataclass
class VerificationResult:
    """Overall verification result."""
    all_pass: bool
    details: list[ArtifactDetail]
    passed_count: int = 0
    total_count: int = 0


class ArtifactVerifier:
    """Verifies that claimed file changes actually exist on disk."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)

    def verify(self, claims: list[ArtifactClaim]) -> VerificationResult:
        """Verify a list of artifact claims."""
        details = []
        for claim in claims:
            file_path = self.base_dir / claim.path
            exists = file_path.exists()

            if claim.action in ("create", "modify"):
                passed = exists
                message = "文件存在" if exists else f"文件不存在: {claim.path}"
            else:
                passed = True
                message = "未知操作，跳过验证"

            details.append(ArtifactDetail(
                path=claim.path,
                action=claim.action,
                exists=exists,
                passed=passed,
                message=message,
            ))

        passed_count = sum(1 for d in details if d.passed)
        return VerificationResult(
            all_pass=all(d.passed for d in details),
            details=details,
            passed_count=passed_count,
            total_count=len(details),
        )

    def format_table(self, result: VerificationResult) -> str:
        """Format verification results as a markdown table."""
        lines = ["#### 产物验证", ""]
        lines.append("| 文件 | 操作 | 存在 | 状态 |")
        lines.append("|------|------|------|------|")
        for d in result.details:
            exists_icon = "✅" if d.exists else "❌"
            status_icon = "通过" if d.passed else "失败"
            lines.append(f"| {d.path} | {d.action} | {exists_icon} | {status_icon} |")
        lines.append(f"\n产物完整性: {result.passed_count}/{result.total_count} 通过")
        return "\n".join(lines)
