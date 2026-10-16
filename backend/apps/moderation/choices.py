"""Справочник причин жалобы (отдаётся клиенту в /api/meta/ как report_reasons)."""

REPORT_REASONS = [
    ("fake_profile", "Fake profile"),
    ("spam", "Spam"),
    ("inappropriate", "Inappropriate content"),
    ("harassment", "Harassment"),
    ("underage", "User may be underage"),
    ("other", "Other"),
]

# Причины, которые модератор разбирает первыми (порядок в админке)
URGENT_REASONS = ("underage", "harassment")
