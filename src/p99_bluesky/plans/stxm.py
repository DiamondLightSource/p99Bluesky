import math
from collections.abc import Iterator
from typing import Any

import bluesky.plan_stubs as bps
from blueapi.core import MsgGenerator
from ophyd_async.epics.motion import Motor

from p99_bluesky.devices.andor2Ad import Andor2Ad, Andor3Ad
from p99_bluesky.log import LOGGER
from p99_bluesky.plans.fast_scan import fast_scan_grid

"""
set parameter for fast_scan_grid

from detector count time calculate roughly how many data point can be done
if no step size for slow axis
    assuming even distribution of points between two axis and work out the
      step for step motor
from the fast scan speed calculate the motor speed needed to achieve those
 point density.
if it is below the min speed, use min speed and place a warning:
    recalculate the step size to fit within time flame and use min speed
    warning
if it is above the max speed, use max
    increase step size so it finishes on time.
    warning that it will finish early


"""


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
    # step_size: float,
) -> MsgGenerator:
    num_data_point = plan_time / count_time
    scan_range = abs(scan_start - scan_end)
    step_range = abs(step_start - step_end)
    # Assuming ideal step size is evenly distributed points within the two axis.
    ideal_step_size = 1.0 / ((num_data_point / (scan_range * step_range)) ** 0.5)
    ideal_velocity = ideal_step_size / count_time

    LOGGER.info(f"{ideal_step_size} velocity = {ideal_velocity}.")
    velocity, step_size = yield from get_velocity_and_step_size(
        scan_motor, ideal_velocity, ideal_step_size
    )
    LOGGER.info(f"{scan_motor.name} velocity = {velocity}.")
    LOGGER.info(f"{step_motor.name} step size = {step_size}.")
    # yield from bps.abs_set(det.drv.acquire_time, count_time
    num_of_step = math.ceil(step_range / step_size)

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
    max_velocity = yield from bps.rd(scan_motor.max_velocity)
    min_velocity = 0.01  # yield from bps.rd(scan_motor.min_velocity)
    # if motor does not move fast enough increase step_motor step size
    if ideal_velocity > max_velocity:
        step_size = int(ideal_velocity / max_velocity * ideal_step_size)
        ideal_velocity = max_velocity
    # if motor does not move slow enough decrease step_motor step size
    # min_velocity not in motor atm need to add it
    elif ideal_velocity < min_velocity:
        step_size = int(ideal_velocity / min_velocity * ideal_step_size)
        ideal_velocity = min_velocity
    else:
        step_size = ideal_step_size
    return ideal_velocity, step_size
