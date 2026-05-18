import json
from pathlib import Path
from reqflow.core.tracer import Tracer

def test_span_lifecycle(tmp_path):
    tracer = Tracer("test-run", output_dir=str(tmp_path / "traces"))
    root = tracer.start_span("root", input_data={"test": True})
    child = tracer.start_span("child", parent_id=root.span_id)
    tracer.end_span(child.span_id, output="done", status="success")
    tracer.end_span(root.span_id, output="complete", status="success")
    summary = tracer.get_summary()
    assert summary["total_spans"] == 2
    assert summary["failed_spans"] == 0

def test_export(tmp_path):
    tracer = Tracer("test-run", output_dir=str(tmp_path / "traces"))
    span = tracer.start_span("export_test")
    tracer.end_span(span.span_id, output="ok", status="success")
    trace_file = tracer.export()
    assert Path(trace_file).exists()
    data = json.loads(Path(trace_file).read_text())
    assert len(data["spans"]) == 1
