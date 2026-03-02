from app.service import MetricsService

def test_success_rate():
    assert MetricsService().success_rate(3, 4) == 0.75
