from app.demo_data import demo_result


def test_demo_result_has_required_fields():
    result = demo_result("job", "mix", "Pop", "both")
    for key in ["job_id", "mode", "genre", "summary", "scores", "recommendations", "metrics"]:
        assert key in result
