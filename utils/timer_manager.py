# utils/timer_manager.py

import logging
from PySide6.QtCore import QObject, QTimer, Signal

class TimerManager(QObject):
    big_break_signal = Signal()
    short_pause_signal = Signal()
    warning_signal = Signal()

    def __init__(self):
        super().__init__()
        self.big_break_timer = QTimer(self)
        self.big_break_timer.timeout.connect(self.on_big_break_timeout)
        
        self.short_pause_timer = QTimer(self)
        self.short_pause_timer.timeout.connect(self.short_pause_signal.emit)
        
        self.warning_timer = QTimer(self)
        self.warning_timer.timeout.connect(self.warning_signal.emit)
        
        self.warning_time_sec = 30

    def start_big_break_timer(self, interval_min):
        self.big_break_timer.start(interval_min * 60 * 1000)
        self.setup_warning_timer(interval_min)

    def start_short_pause_timer(self, interval_min):
        self.short_pause_timer.start(interval_min * 60 * 1000)

    def stop_big_break_timer(self):
        self.big_break_timer.stop()
        self.warning_timer.stop()

    def stop_short_pause_timer(self):
        self.short_pause_timer.stop()

    def set_warning_time(self, seconds):
        self.warning_time_sec = seconds
        if self.big_break_timer.isActive():
            interval_min = self.big_break_timer.interval() / (60 * 1000)
            self.setup_warning_timer(interval_min)

    def setup_warning_timer(self, interval_min):
        warning_interval_ms = (interval_min * 60 - self.warning_time_sec) * 1000
        if warning_interval_ms > 0:
            self.warning_timer.start(warning_interval_ms)
        else:
            self.warning_timer.stop()

    def on_big_break_timeout(self):
        self.warning_timer.stop()
        self.big_break_signal.emit()

    def postpone_big_break(self, minutes):
        self.big_break_timer.start(minutes * 60 * 1000)
        self.setup_warning_timer(minutes)
        logging.info(f"Большой перерыв отложен на {minutes} минут.")

    def pause_all_timers(self): self.pause_big_break_timer(); self.pause_short_pause_timer()
    def resume_all_timers(self): self.resume_big_break_timer(); self.resume_short_pause_timer()
    def stop_all_timers(self): self.stop_big_break_timer(); self.stop_short_pause_timer()

    def _pause_timer(self, timer):
        if timer.isActive(): timer.setProperty("remaining_time", timer.remainingTime()); timer.stop()
    def _resume_timer(self, timer):
        remaining = timer.property("remaining_time")
        if remaining: timer.start(remaining)

    def pause_big_break_timer(self): self._pause_timer(self.big_break_timer); self._pause_timer(self.warning_timer)
    def resume_big_break_timer(self): self._resume_timer(self.big_break_timer); self._resume_timer(self.warning_timer)
    def pause_short_pause_timer(self): self._pause_timer(self.short_pause_timer)
    def resume_short_pause_timer(self): self._resume_timer(self.short_pause_timer)

    def reset_big_break_timer(self):
        if self.big_break_timer.property("is_paused_by_user"): return
        interval_min = self.big_break_timer.interval() / (60 * 1000)
        self.start_big_break_timer(interval_min)
        logging.info("Таймер большого перерыва перезапущен.")

    def reset_short_pause_timer(self):
        if self.short_pause_timer.property("is_paused_by_user"): return
        interval_min = self.short_pause_timer.interval() / (60 * 1000)
        self.start_short_pause_timer(interval_min)
        logging.info("Таймер короткой паузы перезапущен.")