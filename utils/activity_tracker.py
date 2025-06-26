# utils/activity_tracker.py

from PySide6.QtCore import QObject, QTimer, Signal
from utils.system_utils import get_idle_time_windows

class ActivityTracker(QObject):
    user_inactive = Signal(); user_active = Signal()

    def __init__(self, timeout_minutes=30, is_enabled=True):
        super().__init__()
        self.timeout_seconds = timeout_minutes * 60
        self.is_enabled = is_enabled
        self.is_inactive_state = False
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_activity)

    def check_activity(self):
        if not self.is_enabled: return
        idle_time = get_idle_time_windows()
        if idle_time > self.timeout_seconds:
            if not self.is_inactive_state: self.is_inactive_state = True; self.user_inactive.emit()
        else:
            if self.is_inactive_state: self.is_inactive_state = False; self.user_active.emit()

    def start(self):
        if not self.is_enabled: return
        self.is_inactive_state = False; self.check_timer.start(5000)

    def stop(self): self.check_timer.stop()
    def set_enabled(self, enabled):
        self.is_enabled = enabled
        if not enabled: self.stop()
        else: self.start()