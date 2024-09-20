from collections.abc import Callable

import bluesky.plan_stubs as bps
import bluesky.plans as bp
from blueapi.core import MsgGenerator
from bluesky.preprocessors import (
    finalize_wrapper,
)
from bluesky.protocols import Readable
from dodal.plans.data_session_metadata import attach_data_session_metadata_decorator
from ophyd_async.epics.adcore import SingleTriggerDetector
from ophyd_async.epics.motor import Motor
from pydantic import validate_call

from p99_bluesky.devices.andorAd import Andor2Ad, Andor3Ad
from p99_bluesky.log import LOGGER
from p99_bluesky.plan_stubs.motor_plan import (
    check_within_limit,
    get_motor_positions,
    get_velocity_and_step_size,
)
from p99_bluesky.plans.fast_scan import fast_scan_grid
from p99_bluesky.sim.sim_stages import p99SimMotor
from p99_bluesky.utility.utility import step_size_to_step_num


@attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def grid_scan(
    detectors: list[Readable],
    *args: float | Motor | p99SimMotor,
    snake_axes: bool | None = None,
    per_step: Callable | None = None,
    md: dict | None = None,
) -> MsgGenerator:
    return (
        yield from bp.grid_scan(
            detectors, *args, snake_axes=snake_axes, per_step=per_step, md=md
        )
    )


# @attach_data_session_metadata_decorator()
@validate_call(config={"arbitrary_types_allowed": True})
def stxm_step(
    det: Andor2Ad | Andor3Ad | SingleTriggerDetector,
    count_time: float,
    x_step_motor: Motor | p99SimMotor,
    x_step_start: float,
    x_step_end: float,
    x_step_size: float,
    y_step_motor: Motor | p99SimMotor,
    y_step_start: float,
    y_step_end: float,
    y_step_size: float,
    home: bool = False,
    snake: bool = False,
    per_step: Callable | None = None,
    md: dict | None = None,
) -> MsgGenerator:
    """Effectively the standard Bluesky grid scan adapted to use step size.
     Added a centre option where it will move back to
      where it was before scan start.

    Parameters
    ----------
    det: Andor2Ad | Andor3Ad,
        Area detector.
    count_time: float
        detector count time.
    x_step_motor: Motor,
        Motors
    x_step_start: float,
        Starting position for x_step_motor
    x_step_size: float
        Step size for x motor
    step_end: float,
        Ending position for x_step_motor
    y_step_motor: Motor,
        Motor
    y_step_start: float,
        Start for scanning axis
    y_step_end: float,
        End for scanning axis
    y_step_size: float
        Step size for y motor
    home: bool = False,
        If true move back to position before it scan
    snake_axes: bool = True,
        If true, do grid scan without moving scan axis back to start position.
    per_step:
    md=None,

    """

    # check limit before doing anything
    yield from check_within_limit(
        [
            x_step_start,
            x_step_end,
        ],
        x_step_motor,
    )
    yield from check_within_limit(
        [
            y_step_start,
            y_step_end,
        ],
        y_step_motor,
    )
    # Dictionary to store clean up options
    clean_up_arg: dict = {}
    clean_up_arg["Home"] = home
    if home:
        # Add move back  positon to origin
        clean_up_arg["Origin"] = yield from get_motor_positions(
            x_step_motor, y_step_motor
        )
    # Set count time on detector
    yield from bps.abs_set(det.drv.acquire_time, count_time)
    # add 1 to step number to include the end point
    yield from finalize_wrapper(
        plan=grid_scan(
            [det],
            x_step_motor,
            x_step_start,
            x_step_end,
            step_size_to_step_num(x_step_start, x_step_end, x_step_size) + 1,
            y_step_motor,
            y_step_start,
            y_step_end,
            step_size_to_step_num(y_step_start, y_step_end, y_step_size) + 1,
            snake_axes=snake,
            per_step=per_step,
            md=md,
        ),
        final_plan=clean_up(**clean_up_arg),
    )


def stxm_fast(
    det: Andor2Ad | Andor3Ad | SingleTriggerDetector,
    count_time: float,
    step_motor: Motor,
    step_start: float,
    step_end: float,
    scan_motor: Motor,
    scan_start: float,
    scan_end: float,
    plan_time: float,
    step_size: float | None = None,
    home: bool = False,
    snake_axes: bool = True,
    md: dict | None = None,
) -> MsgGenerator:
    """
    This initiates an STXM scan, targeting a maximum scan speed of around 10Hz.
     It calculates the number of data points achievable based on the detector's count
     time. If no step size is provided, the software aims for a uniform distribution
     of points across the scan area. The scanning motor's speed is then determined using
      the calculated point density. If the desired speed exceeds the motor's limit,
     the maximum speed is used. In this case, the step size is automatically adjusted
     to ensure the scan finishes close to the intended duration.

    Parameters
    ----------
    det: Andor2Ad | Andor3Ad,
        Area detector.
    count_time: float
        detector count time.
    step_motor: Motor,
        Motor for the slow axis
    step_start: float,
        Starting position for step axis
    step_end: float,
        Ending position for step axis
    scan_motor: Motor,
        Motor for the continuously moving axis
    scan_start: float,
        Start for scanning axis
    scan_end: float,
        End for scanning axis
    plan_time: float,
        How long it should take in second
    step_size: float | None = None,
        Optional step size for the slow axis
    home: bool = False,
        If true move back to position before it scan
    snake_axes: bool = True,
        If true, do grid scan without moving scan axis back to start position.
    md=None,

    """
    clean_up_arg: dict = {}
    clean_up_arg["Home"] = home
    yield from check_within_limit(
        [
            scan_start,
            scan_end,
        ],
        scan_motor,
    )
    yield from check_within_limit(
        [
            step_start,
            step_end,
        ],
        step_motor,
    )
    # Add move back  positon to origin
    if home:
        clean_up_arg["Origin"] = yield from get_motor_positions(scan_motor, step_motor)

    scan_range = abs(scan_start - scan_end)
    step_range = abs(step_start - step_end)
    step_motor_speed = yield from bps.rd(step_motor.velocity)
    # get number of data point possible after adjusting plan_time for step movement speed
    num_data_point = (plan_time - step_range / step_motor_speed) / count_time
    # Assuming ideal step size is evenly distributed points within the two axis.
    if step_size is not None:
        ideal_step_size = abs(step_size)
        if step_size == 0:
            ideal_velocity = 0  # ideal_velocity: speed that allow the required step size.
        else:
            ideal_velocity = scan_range / (
                (num_data_point / abs(step_range / ideal_step_size)) * count_time
            )

    else:
        ideal_step_size = 1.0 / ((num_data_point / (scan_range * step_range)) ** 0.5)
        ideal_velocity = ideal_step_size / count_time

    LOGGER.info(
        f"ideal step size = {ideal_step_size} velocity = {ideal_velocity}"
        + f" number of data point {num_data_point}"
    )
    # check the idelocity and step size against max velecity and adject in needed.
    velocity, ideal_step_size = yield from get_velocity_and_step_size(
        scan_motor, ideal_velocity, ideal_step_size
    )
    num_of_step = step_size_to_step_num(step_start, step_end, ideal_step_size)
    LOGGER.info(
        f" step size = {ideal_step_size}, {scan_motor.name}: velocity = {velocity}"
        + f", number of step = {num_of_step}."
    )
    # Set count time on detector
    yield from bps.abs_set(det.drv.acquire_time, count_time)
    yield from finalize_wrapper(
        plan=fast_scan_grid(
            [det],
            step_motor,
            step_start,
            step_end,
            num_of_step,
            scan_motor,
            scan_start,
            scan_end,
            velocity,
            snake_axes=snake_axes,
        ),
        final_plan=clean_up(**clean_up_arg),
    )


def clean_up(**kwargs: dict):
    LOGGER.info(f"Clean up: {list(kwargs)}")
    if kwargs["Home"]:
        # move motor back to stored position
        yield from bps.mov(*kwargs["Origin"])
