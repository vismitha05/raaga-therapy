"""
Shared EEGListener singleton for Flask app.py and FastAPI adaptive backend.
"""

from eeg_listener import EEGListener

_listener: EEGListener | None = None


def get_eeg_listener() -> EEGListener:
    global _listener
    if _listener is None:
        _listener = EEGListener()
        _listener.start()
    return _listener
