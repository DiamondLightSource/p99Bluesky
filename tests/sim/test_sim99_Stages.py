import asyncio

import pytest
from ophyd_async.core import (
    DeviceCollector,
)
from ophyd_async.epics.motion.motor import MotorLimitsException

from p99_bluesky.sim.sim_stages import SimThreeAxisStage


@pytest.fixture
async def sim_motor_step():
    async with DeviceCollector():
        sim_motor_step = SimThreeAxisStage(name="sim_motor", instant=False)

    yield sim_motor_step


async def test_MotorLimitsException(sim_motor_step: SimThreeAxisStage):
    await sim_motor_step.x.max_velocity.set(0.01)
    with pytest.raises(MotorLimitsException):
        await sim_motor_step.x._prepare_velocity(
            start_position=2, end_position=5, time_for_move=0.1
        )
    await sim_motor_step.x.low_limit_travel.set(20)
    with pytest.raises(MotorLimitsException):
        await sim_motor_step.x._prepare_motor_path(
            fly_velocity=0.1, start_position=1, end_position=5
        )


async def test_Motor_stop(sim_motor_step: SimThreeAxisStage):
    sim_motor_step.x._set_success = False
    with pytest.raises(RuntimeError):
        move_status = sim_motor_step.x.set(21)
        await asyncio.sleep(0.001)
        await sim_motor_step.x.stop(success=False)
        await move_status
