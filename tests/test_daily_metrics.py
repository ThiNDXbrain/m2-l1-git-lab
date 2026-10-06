"""Tests for the pinned contract events -> daily_metrics, run on SQLite."""
import sqlite3
import unittest

EVENTS = [
    (1, 10, "purchase", "2026-10-01 08:00:00"),
    (2, 11, "purchase", "2026-10-01 09:30:00"),
    (3, 10, "view", "2026-10-01 10:00:00"),
    (4, 12, "purchase", "2026-10-02 11:00:00"),
    (5, 12, "view", "2026-09-30 23:00:00"),
]

BUILD_DAILY_METRICS = """
INSERT INTO daily_metrics (metric_date, event_type, event_count, user_count)
SELECT DATE(event_ts), event_type, COUNT(*), COUNT(DISTINCT user_id)
FROM events
GROUP BY DATE(event_ts), event_type
"""


class DailyMetricsTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute(
            "CREATE TABLE events (event_id INTEGER PRIMARY KEY, user_id INTEGER, "
            "event_type TEXT, event_ts TEXT)"
        )
        self.db.execute(
            "CREATE TABLE daily_metrics (metric_date TEXT, event_type TEXT, "
            "event_count INTEGER, user_count INTEGER, "
            "PRIMARY KEY (metric_date, event_type))"
        )
        self.db.executemany("INSERT INTO events VALUES (?, ?, ?, ?)", EVENTS)
        self.db.execute(BUILD_DAILY_METRICS)

    def tearDown(self):
        self.db.close()

    def test_filter(self):
        rows = self.db.execute(
            "SELECT event_id FROM events "
            "WHERE event_type = 'purchase' AND event_ts >= '2026-10-01' "
            "ORDER BY event_id"
        ).fetchall()
        self.assertEqual(rows, [(1,), (2,), (4,)])

    def test_join_keeps_event_grain(self):
        joined = self.db.execute(
            "SELECT COUNT(*) FROM events e JOIN daily_metrics m "
            "ON m.metric_date = DATE(e.event_ts) AND m.event_type = e.event_type"
        ).fetchone()[0]
        self.assertEqual(joined, len(EVENTS))

    def test_aggregate(self):
        rows = self.db.execute(
            "SELECT metric_date, event_type, event_count, user_count "
            "FROM daily_metrics ORDER BY metric_date, event_type"
        ).fetchall()
        self.assertEqual(
            rows,
            [
                ("2026-09-30", "view", 1, 1),
                ("2026-10-01", "purchase", 2, 2),
                ("2026-10-01", "view", 1, 1),
                ("2026-10-02", "purchase", 1, 1),
            ],
        )

    def test_wrong_grain_inflates_total(self):
        correct = self.db.execute(
            "SELECT SUM(event_count) FROM daily_metrics"
        ).fetchone()[0]
        wrong = self.db.execute(
            "SELECT SUM(m.event_count) FROM events e JOIN daily_metrics m "
            "ON m.metric_date = DATE(e.event_ts) AND m.event_type = e.event_type"
        ).fetchone()[0]
        self.assertEqual(correct, len(EVENTS))
        self.assertEqual(wrong, 7)
        self.assertGreater(wrong, correct)


if __name__ == "__main__":
    unittest.main()
