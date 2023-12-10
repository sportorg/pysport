import time

from sportorg.modules.live.live import LiveThread


def test_live_thread():
    result = []

    async def test(session):
        assert session is not None
        result.append(1)

    live_thread = LiveThread()
    live_thread.start()
    live_thread.send(test)
    time.sleep(1)
    live_thread.stop()
    live_thread.join()
    assert result == [1]
