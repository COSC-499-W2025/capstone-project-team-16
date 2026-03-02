class MetricsService:
    def success_rate(self, ok, total):
        return 0 if total == 0 else ok / total
