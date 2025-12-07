from sportorg.common.otime import OTime
from sportorg.language import translate
from sportorg.models.memory import (
    ResultSportident,
    Person,
    ResultStatus,
    Organization,
    Group,
    race,
)
from sportorg.modules.backup.sfr_results_board import get_srb_line_for_result


def test_srb_generation():
    res = ResultSportident()
    res.place = 12
    res.finish_time = OTime(hour=12, minute=58, sec=59)

    person = Person()
    person.name = "Sergei"
    person.surname = "Petrov"
    person.set_bib(2023)
    res.person = person

    group = Group()
    group.name = "ME"
    person.group = group

    team = Organization()
    team.name = "SKI Team"
    person.organization = team

    line = get_srb_line_for_result(res, "\t", False, False, False)
    assert line == "2023\tME\t009999912:58:59\t1\tPetrov Sergei\tSKI Team\t12:58:59\n"

    res.rogaine_score = 300
    race().set_setting("result_processing_mode", "scores")
    line = get_srb_line_for_result(res, "\t", True, False, False)
    assert (
        line
        == f"2023\tME\t0099699300 {translate('points')} 12:58:59\t1\tPetrov Sergei\tSKI Team\t300 {translate('points')} 12:58:59\n"
    )

    res.scores_ardf = 500
    race().set_setting("result_processing_mode", "ardf")
    line = get_srb_line_for_result(res, "\t", False, True, False)
    assert (
        line
        == f"2023\tME\t0099499500 {translate('points')} 12:58:59\t1\tPetrov Sergei\tSKI Team\t500 {translate('points')} 12:58:59\n"
    )

    race().set_setting("result_processing_mode", "time")
    line = get_srb_line_for_result(res, "\t", False, False, True)
    assert line == "2023\tME\t029999912:58:59\t1\tPetrov Sergei\tSKI Team\t12:58:59\n"

    person.is_out_of_competition = True
    line = get_srb_line_for_result(res, "\t", False, False, False)
    assert line == "2023\tME\t009999912:58:59\t0\tPetrov Sergei\tSKI Team\t12:58:59\n"

    person.is_out_of_competition = False
    res.status = ResultStatus.MISSING_PUNCH
    res.status_comment = "DSQ"
    line = get_srb_line_for_result(res, "\t", False, False, False)
    assert line == "2023\tME\t0099999DSQ\t0\tPetrov Sergei\tSKI Team\tDSQ\n"
