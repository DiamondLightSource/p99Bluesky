from pathlib import Path

import pytest
from bluesky.run_engine import RunEngine
from ophyd.sim import SynPeriodicSignal
from ophyd_async.core import (
    DeviceCollector,
    set_mock_value,
)
from ophyd_async.core.mock_signal_utils import get_mock_put

from p99_bluesky.devices.andor2Ad import Andor2Ad, StaticDirectoryProviderPlus
from p99_bluesky.devices.stages import ThreeAxisStage
from p99_bluesky.plans.fast_scan import fast_scan_1d, fast_scan_grid

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001

CURRENT_DIRECTORY = Path(__file__).parent


async def make_andor2(prefix: str = "") -> Andor2Ad:
    dp = StaticDirectoryProviderPlus(CURRENT_DIRECTORY, "test-")

    async with DeviceCollector(mock=True):
        detector = Andor2Ad(prefix, dp, "andor2")
    return detector


@pytest.fixture
async def andor2() -> Andor2Ad:
    andor2 = await make_andor2(prefix="TEST")

    set_mock_value(andor2._controller.driver.array_size_x, 10)
    set_mock_value(andor2._controller.driver.array_size_y, 20)
    set_mock_value(andor2.hdf.file_path_exists, True)
    set_mock_value(andor2.hdf.num_captured, 0)
    set_mock_value(andor2.hdf.file_path, str(CURRENT_DIRECTORY))
    # assert "test-andor2-hdf0" == await andor2.hdf.file_name.get_value()
    set_mock_value(
        andor2.hdf.full_file_name, str(CURRENT_DIRECTORY) + "/test-andor2-hdf0"
    )
    return andor2


@pytest.fixture
async def sim_motor():
    async with DeviceCollector(mock=True):
        sim_motor = ThreeAxisStage("BLxxI-MO-TABLE-01:X", name="sim_motor")
    set_mock_value(sim_motor.x.velocity, 2.78)
    set_mock_value(sim_motor.x.high_limit_travel, 8.168)
    set_mock_value(sim_motor.x.low_limit_travel, -8.888)
    set_mock_value(sim_motor.x.user_readback, 1)
    set_mock_value(sim_motor.x.motor_egu, "mm")
    set_mock_value(sim_motor.x.motor_done_move, True)
    set_mock_value(sim_motor.y.motor_egu, "mm")
    set_mock_value(sim_motor.y.high_limit_travel, 5.168)
    set_mock_value(sim_motor.y.low_limit_travel, -5.888)
    set_mock_value(sim_motor.y.user_readback, 0)
    set_mock_value(sim_motor.y.motor_egu, "mm")
    set_mock_value(sim_motor.y.velocity, 2.88)
    set_mock_value(sim_motor.y.motor_done_move, True)
    yield sim_motor


async def test_fast_scan_1d_fail_limit_check(
    sim_motor: ThreeAxisStage, RE: RunEngine, andor2: Andor2Ad
):
    det = SynPeriodicSignal(name="rand", labels={"detectors"})
    with pytest.raises(ValueError):
        RE(fast_scan_1d([det], sim_motor.x, 8, 20, 10))

    with pytest.raises(ValueError):
        RE(fast_scan_1d([det], sim_motor.x, -208, 0, 10))

    assert 0 == get_mock_put(sim_motor.x.user_setpoint).call_count


async def test_fast_scan_1d_success(
    sim_motor: ThreeAxisStage, RE: RunEngine, andor2: Andor2Ad
):
    det = SynPeriodicSignal(name="rand", labels={"detectors"})
    RE(fast_scan_1d([det], sim_motor.x, 5, -1, 10))

    assert 2.78 == await sim_motor.x.velocity.get_value()
    assert 2 == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 2 == get_mock_put(sim_motor.x.velocity).call_count


async def test_fast_scan_2d_success(
    sim_motor: ThreeAxisStage, RE: RunEngine, andor2: Andor2Ad
):
    det = SynPeriodicSignal(name="rand", labels={"detectors"})
    step = 5
    RE(fast_scan_grid([det], sim_motor.x, 0, 2, step, sim_motor.y, -0, -5, 1))

    assert 2.78 == await sim_motor.x.velocity.get_value()
    assert step == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 0 == get_mock_put(sim_motor.x.velocity).call_count
    assert 2.88 == await sim_motor.y.velocity.get_value()
    assert step * 2 == get_mock_put(sim_motor.y.user_setpoint).call_count
    assert step * 2 == get_mock_put(sim_motor.y.velocity).call_count
