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

    """

    scan_range = abs(scan_start - scan_end)
    step_range = abs(step_start - step_end)
    step_motor_speed = yield from bps.rd(step_motor.velocity)

    # get number of data point possible after adjusting plan_time for step movement speed
    num_data_point = (plan_time - step_range / step_motor_speed) / count_time

    # Assuming ideal step size is evenly distributed points within the two axis.
    if step_size is not None:
        ideal_step_size = abs(step_size)
        if step_size == 0:
            ideal_velocity = 0  # zero step size
        else:
            ideal_velocity = scan_range / (
                (num_data_point / abs(step_range / ideal_step_size)) * count_time
            )

    else:
        ideal_step_size = 1.0 / ((num_data_point / (scan_range * step_range)) ** 0.5)
        ideal_velocity = ideal_step_size / count_time

    LOGGER.info(
        f"ideal step size = {ideal_step_size} velocity = {ideal_velocity}"
        + f"number of data point {num_data_point}"
    )
    velocity, ideal_step_size = yield from get_velocity_and_step_size(
        scan_motor, ideal_velocity, ideal_step_size
    )
    LOGGER.info(f"{scan_motor.name} velocity = {velocity}.")
    LOGGER.info(f"{step_motor.name} step size = {ideal_step_size}.")
    # Set count time on detector
    yield from bps.abs_set(det.drv.acquire_time, count_time)
    num_of_step = ceil(step_range / ideal_step_size)
    LOGGER.info(f"{step_motor.name} number of step = {num_of_step}.")
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
    scan_motor: Motor, ideal_velocity: float, ideal_step_size: float
) -> Iterator[Any]:
    """Adjust the step size if the required velocity is higher than max value.

    Parameters
    ----------
    scan_motor: Motor,
        The motor which will move continuously.
    ideal_velocity: float
        The velocity wanted.
    ideal_step_size: float
        The non-scanning motor step size.
    """
    if ideal_velocity <= 0.0:
        raise ValueError(f"{scan_motor.name} speed: {ideal_velocity} <= 0")
    max_velocity = yield from bps.rd(scan_motor.max_velocity)
    # if motor does not move fast enough increase step_motor step size
    if ideal_velocity > max_velocity:
        ideal_step_size = ideal_velocity / max_velocity * ideal_step_size
        ideal_velocity = max_velocity

    return ideal_velocity, ideal_step_size
