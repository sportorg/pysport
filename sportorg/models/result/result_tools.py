import logging
import time
from functools import wraps
from typing import Iterable, List, Optional

from sportorg.common.otime import OTime
from sportorg.models.memory import Group, Race, race
from sportorg.models.result.result_calculation import (
    RaceCalculationContext,
    ResultCalculation,
)
from sportorg.models.result.result_checker import ResultChecker
from sportorg.models.result.score_calculation import ScoreCalculation
from sportorg.models.result.split_calculation import RaceSplits

TIMING = {}
FUNCTIONS = {}


def _register(func_name: str):
    def decorator_register(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if func.__name__ not in FUNCTIONS:
                FUNCTIONS[func.__name__] = func_name
            return func(*args, **kwargs)

        return wrapper

    return decorator_register


def _measure_calc_performance(func):
    """
    Decorator to measure the performance of a function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if func.__name__ in "recalculate_results":
            TIMING.clear()

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time_ms = (end_time - start_time) * 1000

        TIMING[func.__name__] = run_time_ms
        if func.__name__ in "recalculate_results":
            timings = ", ".join(
                [f"{FUNCTIONS.get(k, k)}: {v:6.1f} ms" for k, v in TIMING.items()]
            )
            logging.debug("Results recalculation (%s)", timings)
        return result

    return wrapper


@_register("Total")
@_measure_calc_performance
def recalculate_results(
    race_object: Optional[Race] = None,
    group: Optional[Group] = None,
    recheck_results: bool = True,
    groups: Optional[Iterable[Group]] = None,
) -> None:
    """
    Recalculates all results and scores for the specified race

    Args:
        race_object (Race, optional): The race object to process. If None, uses the current race
        group (Group, optional): The group to process. If None, processes all groups
        recheck_results (bool, optional): If True, checks results before recalculating
        groups (Iterable[Group], optional): Groups to process during a partial recalculation

    This function performs the following steps:

    1. Clears existing results for the race
    2. Checks all results
    3. Recalculates results
    4. Generates race splits
    5. Calculates scores
    """

    if race_object is None:
        race_object = race()

    if groups is None:
        affected_groups = [group] if group is not None else None
    else:
        affected_groups = list(dict.fromkeys(groups))
        if group is not None and group not in affected_groups:
            affected_groups.insert(0, group)

    context = RaceCalculationContext(race_object)
    if affected_groups is not None:
        context.invalidate_groups(affected_groups)
        _clear_group_results(race_object, affected_groups)
        _check_groups(race_object, affected_groups, recheck_results)
        _process_group_results(context, affected_groups)
        for affected_group in affected_groups:
            _generate_race_splits(race_object, affected_group, context)
            _calculate_group_scores(race_object, affected_group, context)
    else:
        _clear_results(race_object)
        _check_all(recheck_results)
        _process_results(race_object, context)
        _generate_race_splits(race_object, group, context)
        _calculate_scores(race_object, context)


@_register("Clear")
@_measure_calc_performance
def _clear_results(race_object: Race) -> None:
    race_object.clear_results()


@_register("Clear")
@_measure_calc_performance
def _clear_group_results(race_object: Race, groups: Iterable[Group]) -> None:
    groups = set(groups)
    for result in race_object.results:
        if result.person and result.person.group in groups:
            result.clear()


@_register("Check")
@_measure_calc_performance
def _check_all(recheck_results: bool) -> None:
    if recheck_results:
        ResultChecker.check_all()


@_register("Check")
@_measure_calc_performance
def _check_groups(
    race_object: Race, groups: Iterable[Group], recheck_results: bool
) -> None:
    if not recheck_results:
        return
    groups = set(groups)
    for result in race_object.results:
        if result.person and result.person.group in groups:
            ResultChecker.checking(result)


@_register("Process")
@_measure_calc_performance
def _process_results(
    race_object: Race, context: Optional[RaceCalculationContext] = None
) -> None:
    ResultCalculation(race_object, context).process_results()


@_register("Process")
@_measure_calc_performance
def _process_group_results(
    context: RaceCalculationContext, groups: List[Group]
) -> None:
    ResultCalculation(context.race, context).process_results(groups=groups)


@_register("Splits")
@_measure_calc_performance
def _generate_race_splits(
    race_object: Race,
    group: Optional[Group],
    context: Optional[RaceCalculationContext] = None,
) -> None:
    calculation = ResultCalculation(race_object, context)
    RaceSplits(race_object, calculation).generate(group=group)


@_register("Scores")
@_measure_calc_performance
def _calculate_scores(
    race_object: Race, context: Optional[RaceCalculationContext] = None
) -> None:
    ScoreCalculation(race_object, context).calculate_scores()


@_register("Scores")
@_measure_calc_performance
def _calculate_group_scores(
    race_object: Race, group: Group, context: RaceCalculationContext
) -> None:
    score_calculation = ScoreCalculation(race_object, context)
    for result in ResultCalculation(race_object, context).get_group_finishes(group):
        score_calculation.calculate_scores_result(result)


def change_control_time(control_number: int, add: bool, time: OTime) -> None:
    """
    Changes the control time for a specified control number in read cards

    Args:
        control_number (int): The control number whose time is to be changed
        add (bool): If True, adds the specified time; if False, subtracts the time
        time (OTime): The amount of time to add or subtract

    Returns:
        None
    """
    control_number = str(control_number)
    for result in race().results:
        for control in result.splits:
            if control.code == control_number:
                if add:
                    control.time += time
                else:
                    control.time -= time

    recalculate_results()
