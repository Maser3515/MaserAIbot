"""Analytics service for recording and querying events.

Currently, event logging is handled directly in `database.log_event`. This
module can be extended in the future to perform more complex
analysis such as conversion funnels, time series or custom reports.
"""


def dummy():
    return None