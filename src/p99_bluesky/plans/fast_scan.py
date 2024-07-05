from typing import Any

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from blueapi.core import MsgGenerator
from bluesky.preprocessors import (
    finalize_wrapper,
)
from ophyd_async.epics.motion import Motor

from p99_bluesky.log import LOGGER
from p99_bluesky.plan_stubs.motor_plan import check_within_limit


def fast_scan_1d(
    dets: list[Any],
    motor: Motor,
    start: float,
    end: float,
    motor_speed: float | None = None,
) -> MsgGenerator:
    """
    One axis fast scan

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    motor : Motor (moveable, readable)

    start: float
        starting position.
    end: float,
        ending position

    motor_speed: Optional[float] = None,
        The speed of the motor during scan
    """

    @bpp.stage_decorator(dets)
    @bpp.run_decorator()
    def inner_fast_scan_1d(
        dets: list[Any],
        motor: Motor,
        start: float,
        end: float,
        motor_speed: float | None = None,
    ):
        yield from check_within_limit([start, end], motor)
        yield from _fast_scan_1d(dets, motor, start, end, motor_speed)

    yield from finalize_wrapper(
        plan=inner_fast_scan_1d(dets, motor, start, end, motor_speed),
        final_plan=clean_up(),
    )


def fast_scan_grid(
    dets: list[Any],
    step_motor: Motor,
    step_start: float,
    step_end: float,
    num_step: int,
    scan_motor: Motor,
    scan_start: float,
    scan_end: float,
    motor_speed: float | None = None,
    snake_axes: bool = False,
) -> MsgGenerator:
    """
    Same as fast_scan_1d with an extra axis to step through forming a grid

     Parameters
     ----------
     detectors : list
         list of 'readable' objects
     step_motor : Motor (moveable, readable)
     scan_motor:  Motor (moveable, readable)
     start: float
         starting position.
     end: float,
         ending position

     motor_speed: Optional[float] = None,
         The speed of the motor during scan
    """

    @bpp.stage_decorator(dets)
    @bpp.run_decorator()
    def inner_fast_scan_grid(
        dets: list[Any],
        step_motor: Motor,
        step_start: float,
        step_end: float,
        num_step: int,
        scan_motor: Motor,
        scan_start: float,
        scan_end: float,
        motor_speed: float | None = None,
        snake_axes: bool = False,
    ):
        yield from check_within_limit([step_start, step_end], step_motor)
        yield from check_within_limit([scan_start, scan_end], scan_motor)
        step_size = (step_end - step_start) / num_step
        step_counter = 1
        current_step = step_start + step_size * step_counter
        if snake_axes:
            while num_step >= step_counter:
                yield from bps.mv(step_motor, current_step)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_start, scan_end, motor_speed
                )
                step_counter += 1
                current_step = step_start + step_size * step_counter
                yield from bps.mv(step_motor, current_step)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_end, scan_start, motor_speed
                )
                step_counter += 1
                current_step = step_start + step_size * step_counter
        else:
            while num_step >= step_counter:
                yield from bps.mv(step_motor, current_step)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_start, scan_end, motor_speed
                )
                step_counter += 1
                current_step = step_start + step_size * step_counter

    yield from finalize_wrapper(
        plan=inner_fast_scan_grid(
            dets,
            step_motor,
            step_start,
            step_end,
            num_step,
            scan_motor,
            scan_start,
            scan_end,
            motor_speed,
            snake_axes,
        ),
        final_plan=clean_up(),
    )


def _fast_scan_1d(
    dets: list[Any],
    motor: Motor,
    start: float,
    end: float,
    motor_speed: float | None = None,
) -> MsgGenerator:
    """
    The logic for one axis fast scan, see fast_scan_1d and fast_scan_grid

    In this scan:
    1) The motor moves to the starting point.
    2) The motor speed is changed
    3) The motor is set in motion toward the end point
    4) During this movement detectors are triggered and read out until
      the endpoint is reached or stopped.
    5) Clean up, reset motor speed.

    Note: This is purely software triggering which result in variable accuracy.
    However, fast scan does not require encoder and hardware setup and should
    work for all motor. It is most frequently use for alignment and
      slow motion measurements.

    Parameters
    ----------
    detectors : list
        list of 'readable' objects
    motor : Motor (moveable, readable)

    start: float
        starting position.
    end: float,
        ending position

    motor_speed: Optional[float] = None,
        The speed of the motor during scan
    """

    # read the current speed and store it
    old_speed = yield from bps.rd(motor.velocity)

    def inner_fast_scan_1d(
        dets: list[Any],
        motor: Motor,
        start: float,
        end: float,
        motor_speed: float | None = None,
    ):
        LOGGER.info(f"Moving {motor.name} to start position = {start}.")
        yield from bps.mv(motor, start)  # move to start

        if motor_speed:
            LOGGER.info(f"Set {motor.name} speed = {motor_speed}.")
            yield from bps.abs_set(motor.velocity, motor_speed)

        LOGGER.info(f"Set {motor.name} to end position({end}) and begin scan.")
        yield from bps.abs_set(motor.user_setpoint, end)
        # yield from bps.wait_for(motor.motor_done_move, False)
        done = False

        while not done:
            yield from bps.trigger_and_read(dets + [motor])
            done = yield from bps.rd(motor.motor_done_move)
            yield from bps.checkpoint()

    yield from finalize_wrapper(
        plan=inner_fast_scan_1d(dets, motor, start, end, motor_speed),
        final_plan=reset_speed(old_speed, motor),
    )


def reset_speed(old_speed, motor: Motor):
    LOGGER.info(f"Clean up: setting motor speed to {old_speed}.")
    if old_speed:
        yield from bps.abs_set(motor.velocity, old_speed)


def clean_up():
    LOGGER.info("Clean up")
    # possibly use to move back to starting position.
    yield from bps.null()
