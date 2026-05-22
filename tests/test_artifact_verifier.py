"""Tests for ArtifactVerifier — file existence + content verification."""

import pytest
from pathlib import Path
from core.artifact_verifier import ArtifactVerifier, ArtifactClaim, VerificationResult


def test_verify_existing_file(tmp_path):
    """Should pass for existing file with matching action."""
    test_file = tmp_path / "test.py"
    test_file.write_text("hello")
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="test.py", action="create")]
    result = verifier.verify(claims)
    assert result.all_pass
    assert len(result.details) == 1
    assert result.details[0].passed


def test_verify_missing_file(tmp_path):
    """Should fail for missing file."""
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="missing.py", action="create")]
    result = verifier.verify(claims)
    assert not result.all_pass
    assert not result.details[0].passed


def test_verify_modify_existing(tmp_path):
    """Should pass for modify action when file exists."""
    test_file = tmp_path / "existing.py"
    test_file.write_text("content")
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="existing.py", action="modify")]
    result = verifier.verify(claims)
    assert result.all_pass


def test_verify_modify_missing(tmp_path):
    """Should fail for modify action when file does not exist."""
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="missing.py", action="modify")]
    result = verifier.verify(claims)
    assert not result.all_pass


def test_format_verification_table(tmp_path):
    """Should format results as a markdown table."""
    test_file = tmp_path / "test.py"
    test_file.write_text("hello")
    verifier = ArtifactVerifier(base_dir=str(tmp_path))
    claims = [ArtifactClaim(path="test.py", action="create")]
    result = verifier.verify(claims)
    table = verifier.format_table(result)
    assert "产物验证" in table
    assert "test.py" in table
    assert "✅" in table
