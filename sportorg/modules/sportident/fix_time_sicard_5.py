from sportorg.common.otime import OTime

DEF_START_TIME = OTime(hour=8)


def if_si_card_5(card_number):
    return card_number < 1000000


def _fix_time(time, zero_time):
    """
    takes nearest to zero time, assuming, that original time is in only 12h format (SPORTident SICard 5)
    exclude 00:00:00, meaning no time
    00:15:18 (10:00:00) -> 12:15:18
    00:15:18 (14:00:00) -> 00:15:18
    11:15:18 (10:00:00) -> 11:15:18
    11:15:18 (17:00:00) -> 23:15:18
    22:15:18 (10:00:00) -> 10:15:18
    22:15:18 (11:00:00) -> 22:15:18
    """
    origin_time = time

    if time == OTime(0):
        return time

    time_12h = OTime(hour=12)

    if time >= time_12h:
        time -= time_12h

    if zero_time > time:
        if zero_time - time < time_12h:
            time += time_12h

    return time


# fix time in result for SI Card 5 (12h format)
def fix_time(res, zero_time=DEF_START_TIME):
    if if_si_card_5(res.card_number):
        res.finish_time = _fix_time(res.finish_time, zero_time)
        res.start_time = _fix_time(res.start_time, zero_time)

        for i in range(len(res.splits)):
            res.splits[i].time = _fix_time(res.splits[i].time, zero_time)
