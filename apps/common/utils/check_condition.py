from .format_data import format_by_raw_and_summary


def is_failed_status_by_summary(summary):
    return summary.get("success") is not True or len(summary.get("dark")) > 0


def is_failed_status_by_summary_and_raw(raw, summary):
    format_data = format_by_raw_and_summary(raw=raw, summary=summary)
    return format_data['success'] is False


def is_success_by_summary_and_raw(raw, summary):
    format_data = format_by_raw_and_summary(raw=raw, summary=summary)
    return format_data['success']
