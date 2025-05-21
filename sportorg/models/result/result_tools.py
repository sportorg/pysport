import logging
import time
from functools import wraps

from sportorg.common.otime import OTime
from sportorg.models.memory import Group, Race, race
from sportorg.models.result.result_calculation import ResultCalculation
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
    race_object: Race = None, group: Group = None, recheck_results: bool = True
) -> None:
    """
    Recalculates all results and scores for the specified race

    Args:
        race_object (Race, optional): The race object to process. If None, uses the current race
        group (Group, optional): The group to process. If None, processes all groups
        recheck_results (bool, optional): If True, checks all results before recalculating

    This function performs the following steps:

    1. Clears existing results for the race
    2. Checks all results
    3. Recalculates results
    4. Generates race splits
    5. Calculates scores
    """

    if race_object is None:
        race_object = race()

    _clear_results(race_object)
    _check_all(recheck_results)
    _process_results(race_object)
    _generate_race_splits(race_object, group)
    _calculate_scores(race_object)


@_register("Clear")
@_measure_calc_performance
def _clear_results(race_object: Race) -> None:
    race_object.clear_results()


@_register("Check")
@_measure_calc_performance
def _check_all(recheck_results: bool) -> None:
    if recheck_results:
        ResultChecker.check_all()


@_register("Process")
@_measure_calc_performance
def _process_results(race_object: Race) -> None:
    ResultCalculation(race_object).process_results()


@_register("Splits")
@_measure_calc_performance
def _generate_race_splits(race_object: Race, group: Group) -> None:
    RaceSplits(race_object).generate(group=group)


@_register("Scores")
@_measure_calc_performance
def _calculate_scores(race_object: Race) -> None:
    ScoreCalculation(race_object).calculate_scores()


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
