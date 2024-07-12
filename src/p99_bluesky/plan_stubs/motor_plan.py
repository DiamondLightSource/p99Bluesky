import bluesky.plan_stubs as bps
from ophyd_async.epics.motion import Motor

from p99_bluesky.log import LOGGER


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
