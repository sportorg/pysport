from sportorg import settings
from sportorg.common.audio import Audio
from sportorg.common.singleton import singleton


@singleton
class Sound:
    @staticmethod
    def is_enabled():
        return settings.SETTINGS.sound_enabled

    @staticmethod
    def is_enabled_rented_card():
        return settings.SETTINGS.sound_rented_card_enabled

    def _play(self, sound_path: str) -> None:
        if self.is_enabled() and sound_path:
            Audio().play(sound_path)

    def ok(self):
        self._play(settings.successful_sound_path())

    def fail(self):
        self._play(settings.unsuccessful_sound_path())

    def rented_card(self):
        if self.is_enabled_rented_card():
            self._play(settings.rented_card_sound_path())

    def enter_number(self):
        self._play(settings.enter_number_sound_path())
