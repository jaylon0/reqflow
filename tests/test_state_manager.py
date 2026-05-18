from reqflow.core.state_manager import StateManager

def test_state_initial(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    assert sm.state.run_id
    assert sm.state.current_stage == ""

def test_update_stage(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    sm.update_stage("analyze")
    assert sm.state.current_stage == "analyze"

def test_complete_module(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    sm.complete_module("mod_a")
    sm.complete_module("mod_b")
    assert "mod_a" in sm.state.completed_modules
    assert "mod_b" in sm.state.completed_modules

def test_checkpoint_create_restore(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    cp = sm.create_checkpoint("test_stage", context={"key": "value"})
    assert cp.checkpoint_id
    assert cp.stage == "test_stage"
    restored_state, restored_ctx = sm.restore_checkpoint(cp.checkpoint_id)
    assert restored_ctx["key"] == "value"

def test_persistence(tmp_run_dir):
    sm = StateManager(tmp_run_dir)
    sm.update_stage("persist_test")
    sm.complete_module("mod_x")
    sm.save_state()
    sm2 = StateManager(tmp_run_dir)
    assert sm2.state.current_stage == "persist_test"
    assert "mod_x" in sm2.state.completed_modules
