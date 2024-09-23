import asyncio
import contextlib

from bluesky.protocols import Flyable, Preparable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    WatchableAsyncStatus,
    observe_value,
    soft_signal_rw,
)
from ophyd_async.core._utils import (
    WatcherUpdate,
)
from ophyd_async.epics.motor import FlyMotorInfo, MotorLimitsException
from ophyd_async.sim.demo._sim_motor import SimMotor


class p99SimMotor(SimMotor, Flyable, Preparable):
    """
    Adding the missing part to the SimMotor so it behave more like motor
    """

    def __init__(self, name="", instant=True) -> None:
        self.max_velocity = soft_signal_rw(float, 100)
        self.acceleration_time = soft_signal_rw(float, 0.0)
        self.precision = soft_signal_rw(int, 3)
        self.deadband = soft_signal_rw(float, 0.05)
        self.motor_done_move = soft_signal_rw(int, 1)
        self.low_limit_travel = soft_signal_rw(float, -10)
        self.high_limit_travel = soft_signal_rw(float, 10)
        super().__init__(name=name, instant=instant)

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo):
        """Calculate required velocity and run-up distance, then if motor limits aren't
        breached, move to start position minus run-up distance"""

        self._fly_timeout = value.timeout

        # Velocity, at which motor travels from start_position to end_position, in motor
        # egu/s.
        fly_velocity = await self._prepare_velocity(
            value.start_position,
            value.end_position,
            value.time_for_move,
        )

        # start_position with run_up_distance added on.
        fly_prepared_position = await self._prepare_motor_path(
            abs(fly_velocity), value.start_position, value.end_position
        )

        await self.set(fly_prepared_position)

    @AsyncStatus.wrap
    async def kickoff(self):
        """Begin moving motor from prepared position to final position."""
        assert (
            self._fly_completed_position
        ), "Motor must be prepared before attempting to kickoff"

        self._fly_status = self.set(self._fly_completed_position)

    def complete(self) -> WatchableAsyncStatus:
        """Mark as complete once motor reaches completed position."""
        assert self._fly_status, "kickoff not called"
        return self._fly_status

    async def _prepare_velocity(
        self, start_position: float, end_position: float, time_for_move: float
    ) -> float:
        fly_velocity = (start_position - end_position) / time_for_move
        max_speed, egu = await asyncio.gather(
            self.max_velocity.get_value(), self.units.get_value()
        )
        if abs(fly_velocity) > max_speed:
            raise MotorLimitsException(
                f"Motor speed of {abs(fly_velocity)} {egu}/s was requested for a motor "
                f" with max speed of {max_speed} {egu}/s"
            )
        await self.velocity.set(abs(fly_velocity))
        return fly_velocity

    async def _prepare_motor_path(
        self, fly_velocity: float, start_position: float, end_position: float
    ) -> float:
        # Distance required for motor to accelerate from stationary to fly_velocity, and
        # distance required for motor to decelerate from fly_velocity to stationary
        run_up_distance = (await self.acceleration_time.get_value()) * fly_velocity * 0.5
        self._fly_completed_position = end_position + run_up_distance

        # Prepared position not used after prepare, so no need to store in self
        fly_prepared_position = start_position - run_up_distance

        motor_lower_limit, motor_upper_limit, egu = await asyncio.gather(
            self.low_limit_travel.get_value(),
            self.high_limit_travel.get_value(),
            self.units.get_value(),
        )

        if (
            not motor_upper_limit >= fly_prepared_position >= motor_lower_limit
            or not motor_upper_limit >= self._fly_completed_position >= motor_lower_limit
        ):
            raise MotorLimitsException(
                f"Motor trajectory for requested fly is from "
                f"{fly_prepared_position}{egu} to "
                f"{self._fly_completed_position}{egu} but motor limits are "
                f"{motor_lower_limit}{egu} <= x <= {motor_upper_limit}{egu} "
            )
        return fly_prepared_position

    @WatchableAsyncStatus.wrap
    async def set(self, value: float):
        """
        Asynchronously move the motor to a new position.
        """
        # Make sure any existing move tasks are stopped
        await self.stop()
        old_position, units, velocity = await asyncio.gather(
            self.user_setpoint.get_value(),
            self.units.get_value(),
            self.velocity.get_value(),
        )
        # If zero velocity, do instant move
        move_time = abs(value - old_position) / velocity if velocity else 0
        self._move_status = AsyncStatus(self._move(old_position, value, move_time))
        # If stop is called then this will raise a CancelledError, ignore it
        with contextlib.suppress(asyncio.CancelledError):
            async for current_position in observe_value(
                self.user_readback, done_status=self._move_status
            ):
                yield WatcherUpdate(
                    current=current_position,
                    initial=old_position,
                    target=value,
                    name=self.name,
                    unit=units,
                )
        if not self._set_success:
            raise RuntimeError("Motor was stopped")


class SimThreeAxisStage(Device):
    """
    mimic the three axis p99 stage with motor
    """

    def __init__(self, name: str, infix: list[str] | None = None, instant=False):
        if infix is None:
            infix = ["X", "Y", "Z"]
        self.x = p99SimMotor(name + infix[0], instant=instant)
        self.y = p99SimMotor(name + infix[1], instant=instant)
        self.z = p99SimMotor(name + infix[2], instant=instant)
        super().__init__(name=name)
