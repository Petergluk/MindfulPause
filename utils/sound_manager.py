# utils/sound_manager.py

import os
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

class SoundManager:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.end_player, self.end_audio_output = self._create_player('end.mp3')
        self.start_player, self.start_audio_output = self._create_player('start.mp3')

    def _create_player(self, filename):
        player = QMediaPlayer(); audio_output = QAudioOutput()
        player.setAudioOutput(audio_output)
        path = os.path.join(self.base_dir, 'data', 'sound', filename)
        if os.path.exists(path):
            player.setSource(QUrl.fromLocalFile(path)); audio_output.setVolume(0.8)
        else: print(f"ВНИМАНИЕ: Звуковой файл не найден: {path}")
        return player, audio_output

    def play_end_sound(self):
        if self.end_player.source().isValid(): self.end_player.setPosition(0); self.end_player.play()

    def play_start_sound(self):
        if self.start_player.source().isValid(): self.start_player.setPosition(0); self.start_player.play()