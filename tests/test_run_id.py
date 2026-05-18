import shutil
from reqflow.core.engine import Engine
from reqflow.core.runtime_config import RuntimeConfig


def test_run_id_matches_dir_name():
    """run_id should match the directory name."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config, run_dir="/tmp/test-run-id-consistency")
    assert engine.run_id == "test-run-id-consistency"
    shutil.rmtree("/tmp/test-run-id-consistency", ignore_errors=True)


def test_run_id_auto_generated_is_readable():
    """Auto-generated run_id should be human-readable, not UUID."""
    config = RuntimeConfig(name="manual", display_name="Manual")
    engine = Engine(config=config)
    assert "run-" in engine.run_id
    assert len(engine.run_id) < 30  # Not a UUID
    shutil.rmtree(engine.run_dir, ignore_errors=True)
