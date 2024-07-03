import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp
from bluesky.preprocessors import (
    finalize_wrapper,
)
from ophyd_async.epics.motion import Motor
from ophyd_async.protocols import AsyncReadable

from p99_bluesky.log import LOGGER


def fast_scan_1d(
    dets: list[AsyncReadable],
    motor: Motor,
    start: float,
    end: float,
    motor_speed: float | None = None,
):
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
        dets: list[AsyncReadable],
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
    dets: list[AsyncReadable],
    step_motor: Motor,
    step_start: float,
    step_end: float,
    step_size: float,
    scan_motor: Motor,
    scan_start: float,
    scan_end: float,
    motor_speed: float | None = None,
    snake_axes: bool = False,
):
    """
    Same as fast_scan_1d with an extra axis to step through to from a grid

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
        dets: list[AsyncReadable],
        step_motor: Motor,
        step_start: float,
        step_end: float,
        step_number: float,
        scan_motor: Motor,
        scan_start: float,
        scan_end: float,
        motor_speed: float | None = None,
        snake_axes: bool = False,
    ):
        yield from check_within_limit([step_start, step_end], step_motor)
        yield from check_within_limit([scan_start, scan_end], scan_motor)
        step_size = (step_end - step_start) / step_number
        step_counter = 1
        if snake_axes:
            while step_number >= step_counter:
                yield from bps.mv(step_motor, step_start + step_size * step_counter)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_start, scan_end, motor_speed
                )
                step_counter += 1
                yield from bps.mv(step_motor, step_start + step_size * step_counter)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_end, scan_start, motor_speed
                )
                step_counter += 1
        else:
            while step_number >= step_counter:
                yield from bps.mv(step_motor, step_start + step_size * step_counter)
                yield from _fast_scan_1d(
                    dets + [step_motor], scan_motor, scan_start, scan_end, motor_speed
                )
                step_counter += 1

    yield from finalize_wrapper(
        plan=inner_fast_scan_grid(
            dets,
            step_motor,
            step_start,
            step_end,
            step_size,
            scan_motor,
            scan_start,
            scan_end,
            motor_speed,
            snake_axes,
        ),
        final_plan=clean_up(),
    )


def _fast_scan_1d(
    dets: list[AsyncReadable],
    motor: Motor,
    start: float,
    end: float,
    motor_speed: float | None = None,
):
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
        dets: list[AsyncReadable],
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


def check_within_limit(values: list, motor: Motor):
    LOGGER.info(f"Check {motor.name} limits.")
    lower_limit = yield from bps.rd(motor.low_limit_travel)
    high_limit = yield from bps.rd(motor.high_limit_travel)
    for value in values:
        if not lower_limit < value < high_limit:
            raise ValueError(
                f"{motor.name} move request of {value} is beyond limits:"
                f"{lower_limit} < {high_limit}"
            )


def reset_speed(old_speed, motor: Motor):
    LOGGER.info(f"Clean up: setting motor speed to {old_speed}.")
    if old_speed:
        yield from bps.abs_set(motor.velocity, old_speed)


def clean_up():
    LOGGER.info("Clean up")
    # possibly use to move back to starting position.
    yield from bps.null()
