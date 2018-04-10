from sportorg.core.audio import Audio
from sportorg.core.singleton import singleton
from sportorg.modules.configs.configs import Config


@singleton
class Sound(object):
    @staticmethod
    def is_enabled():
        return Config().sound.get('enabled')

    def _play(self, name):
        sound = Config().sound.get(name)
        if self.is_enabled() and sound:
            Audio().play(sound)

    def ok(self):
        self._play('successful')

    def fail(self):
        self._play('unsuccessful')
