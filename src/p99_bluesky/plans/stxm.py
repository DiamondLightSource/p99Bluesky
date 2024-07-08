from collections.abc import Iterator
from math import ceil
from typing import Any

import bluesky.plan_stubs as bps
from blueapi.core import MsgGenerator
from ophyd_async.epics.motion import Motor

from p99_bluesky.devices.andor2Ad import Andor2Ad, Andor3Ad
from p99_bluesky.log import LOGGER
from p99_bluesky.plans.fast_scan import fast_scan_grid


def stxm_fast(
    det: Andor2Ad | Andor3Ad,
    count_time: float,
    step_motor: Motor,
    step_start: float,
    step_end: float,
    scan_motor: Motor,
    scan_start: float,
    scan_end: float,
    plan_time: float,
    step_size: float | None = None,
) -> MsgGenerator:
    """
    Software triggering stxm scan:
    Using detector count time to calculate roughly how many data point can be done
    If no step size is provided use evenly distributed of points if possible,
    the speed of the scanning motor is calculated using the point density.
    If scan motor speed is above its max speed,max speed is used and
     the step size is adjusted so it finishes roughly on time.
    """

    scan_range = abs(scan_start - scan_end)
    step_range = abs(step_start - step_end)
    step_motor_speed = yield from bps.rd(step_motor.velocity)

    # get number of data point possible after adjusting plan_time for step movement speed
    num_data_point = (plan_time - step_motor_speed * step_range) / count_time

    # Assuming ideal step size is evenly distributed points within the two axis.
    if step_size is not None:
        ideal_step_size = step_size
    else:
        ideal_step_size = 1.0 / ((num_data_point / (scan_range * step_range)) ** 0.5)
    ideal_velocity = ideal_step_size / count_time

    LOGGER.info(f"ideal step size = {ideal_step_size} velocity = {ideal_velocity}.")
    velocity, ideal_step_size = yield from get_velocity_and_step_size(
        scan_motor, ideal_velocity, ideal_step_size
    )
    LOGGER.info(f"{scan_motor.name} velocity = {velocity}.")
    LOGGER.info(f"{step_motor.name} step size = {step_size}.")
    # yield from bps.abs_set(det.drv.acquire_time, count_time
    num_of_step = ceil(step_range / ideal_step_size)

    yield from fast_scan_grid(
        [det],
        step_motor,
        step_start,
        step_end,
        num_of_step,
        scan_motor,
        scan_start,
        scan_end,
        velocity,
        snake_axes=True,
    )


def get_velocity_and_step_size(
    scan_motor: Motor, ideal_velocity: float, ideal_step_size
) -> Iterator[Any]:
    print(ideal_velocity)
    if ideal_velocity <= 0.1:
        raise ValueError(f"{scan_motor.name} speed: {ideal_velocity} <= 0")
    max_velocity = yield from bps.rd(scan_motor.max_velocity)
    # if motor does not move fast enough increase step_motor step size
    if ideal_velocity > max_velocity:
        ideal_step_size = ideal_velocity / max_velocity * ideal_step_size
        ideal_velocity = max_velocity

    return ideal_velocity, ideal_step_size
