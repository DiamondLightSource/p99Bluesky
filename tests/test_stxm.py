from collections import defaultdict
from unittest.mock import Mock

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    assert_emitted,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.areadetector.drivers.ad_base import DetectorState

from p99_bluesky.devices.andor2Ad import Andor2Ad, StaticDirectoryProviderPlus
from p99_bluesky.devices.stages import ThreeAxisStage
from p99_bluesky.plans.stxm import stxm_fast, stxm_step
from p99_bluesky.sim.sim_stages import SimThreeAxisStage
from p99_bluesky.utility.utility import step_size_to_step_num


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
    set_mock_value(sim_motor.x.max_velocity, 10)

    set_mock_value(sim_motor.y.motor_egu, "mm")
    set_mock_value(sim_motor.y.high_limit_travel, 5.168)
    set_mock_value(sim_motor.y.low_limit_travel, -5.888)
    set_mock_value(sim_motor.y.user_readback, 0)
    set_mock_value(sim_motor.y.motor_egu, "mm")
    set_mock_value(sim_motor.y.velocity, 2.88)
    set_mock_value(sim_motor.y.motor_done_move, True)
    set_mock_value(sim_motor.y.max_velocity, 10)

    yield sim_motor


@pytest.fixture
async def sim_motor_step():
    async with DeviceCollector():
        sim_motor_step = SimThreeAxisStage(name="sim_motor", instant=True)

    yield sim_motor_step


@pytest.fixture
async def andor2(tmp_path) -> Andor2Ad:
    dp = StaticDirectoryProviderPlus(tmp_path, "test-")
    async with DeviceCollector(mock=True):
        andor2 = Andor2Ad("TEST", dp, "andor2")

    set_mock_value(andor2._controller.driver.array_size_x, 10)
    set_mock_value(andor2._controller.driver.array_size_y, 20)
    set_mock_value(andor2.hdf.file_path_exists, True)
    set_mock_value(andor2.hdf.num_captured, 0)
    set_mock_value(andor2.hdf.file_path, str(tmp_path))
    set_mock_value(andor2.hdf.full_file_name, str(tmp_path) + "/test-andor2-hdf0")
    set_mock_value(andor2.drv.detector_state, DetectorState.Idle)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(0, 1000)
    callback_on_mock_put(
        andor2._writer.hdf.capture,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.capture, value=True),
    )
    callback_on_mock_put(
        andor2.drv.acquire,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.num_captured, rbv_mocks.get()),
    )
    return andor2


async def test_stxm_fast_zero_velocity_fail(
    andor2: Andor2Ad, sim_motor: ThreeAxisStage, RE: RunEngine
):
    plan_time = 30
    count_time = 0.2
    step_size = 0.0
    step_start = -2
    step_end = 3
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    with pytest.raises(ValueError):
        RE(
            stxm_fast(
                det=andor2,
                count_time=count_time,
                step_motor=sim_motor.x,
                step_start=step_start,
                step_end=step_end,
                scan_motor=sim_motor.y,
                scan_start=1,
                scan_end=2,
                plan_time=plan_time,
                step_size=step_size,
            ),
            capture_emitted,
        )
    # should do nothing
    assert_emitted(docs)


async def test_stxm_fast(andor2: Andor2Ad, sim_motor: ThreeAxisStage, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    plan_time = 10
    count_time = 0.2
    step_size = 0.2
    step_start = -2
    step_end = 3
    num_of_step = step_size_to_step_num(step_start, step_end, step_size)
    RE(
        stxm_fast(
            det=andor2,
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=1,
            scan_end=2,
            plan_time=plan_time,
            step_size=step_size,
            home=True,
        ),
        capture_emitted,
    )
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=num_of_step,
        event=num_of_step,
        stop=1,
    )


async def test_stxm_fast_unknown_step(andor2, sim_motor, RE):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    step_motor_speed = 1
    set_mock_value(sim_motor.x.velocity, step_motor_speed)

    step_start = 0
    step_end = 2
    plan_time = 10 + step_motor_speed * abs(step_start - step_end)
    count_time = 0.1

    scan_start = 0
    scan_end = 2
    # make the scan motor slow so it can only do 5 steps
    # ideal step-size is 0.2 with speed =2 for 10x10
    set_mock_value(sim_motor.y.max_velocity, 1)

    # Unknown step size
    docs = defaultdict(list)
    RE(
        stxm_fast(
            det=andor2,
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_start=scan_start,
            scan_end=scan_end,
            scan_motor=sim_motor.y,
            plan_time=plan_time,
        ),
        capture_emitted,
    )
    # speed capped at half ideal so expecting 5 events
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=5,
        event=5,
        stop=1,
    )


async def test_stxm_step_with_home(RE, sim_motor_step, andor2):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    await sim_motor_step.x.set(-1)
    await sim_motor_step.y.set(-2)

    RE(
        stxm_step(
            det=[andor2],
            count_time=0.2,
            x_step_motor=sim_motor_step.x,
            x_step_start=0,
            x_step_end=2,
            x_step_size=0.1,
            y_step_motor=sim_motor_step.y,
            y_step_start=-1,
            y_step_end=1,
            y_step_size=0.5,
            home=True,
            snake=True,
        ),
        capture_emitted,
    )

    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=80,
        event=80,
        stop=1,
    )
    assert -1 == await sim_motor_step.x.user_readback.get_value()
    assert -2 == await sim_motor_step.y.user_readback.get_value()


async def test_stxm_step_without_home(RE, sim_motor_step, andor2):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    # await sim_motor_step.x.set(-1)
    # await sim_motor_step.y.set(-2)
    y_step_end = 1
    x_step_end = 2
    RE(
        stxm_step(
            det=[andor2],
            count_time=0.2,
            x_step_motor=sim_motor_step.x,
            x_step_start=0,
            x_step_end=x_step_end,
            x_step_size=0.1,
            y_step_motor=sim_motor_step.y,
            y_step_start=-1,
            y_step_end=y_step_end,
            y_step_size=0.5,
            home=False,
            snake=False,
        ),
        capture_emitted,
    )
    assert_emitted(
        docs,
        start=1,
        descriptor=1,
        stream_resource=1,
        stream_datum=80,
        event=80,
        stop=1,
    )
    assert x_step_end == await sim_motor_step.x.user_readback.get_value()
    assert y_step_end == await sim_motor_step.y.user_readback.get_value()
