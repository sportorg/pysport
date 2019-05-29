from sportorg.common.audio import Audio
from sportorg.common.singleton import singleton
from sportorg.modules.configs.configs import Config


@singleton
class Sound(object):
    @staticmethod
    def is_enabled():
        return Config().sound.get('enabled')

    @staticmethod
    def is_enabled_rented_card():
        return Config().sound.get('enabled_rented_card')

    def _play(self, name):
        sound = Config().sound.get(name)
        if self.is_enabled() and sound:
            Audio().play(sound)

    def ok(self):
        self._play('successful')

    def fail(self):
        self._play('unsuccessful')

    def rented_card(self):
        if self.is_enabled_rented_card():
            self._play('rented_card')
