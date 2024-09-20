import time
from collections import defaultdict

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    DeviceCollector,
    assert_emitted,
    set_mock_value,
)

from p99_bluesky.devices.andorAd import Andor2Ad, Andor3Ad
from p99_bluesky.devices.stages import ThreeAxisStage
from p99_bluesky.plans.stxm import stxm_fast, stxm_step
from p99_bluesky.sim.sim_stages import SimThreeAxisStage
from p99_bluesky.utility.utility import step_size_to_step_num


@pytest.fixture
async def sim_motor_step():
    async with DeviceCollector():
        sim_motor_step = SimThreeAxisStage(name="sim_motor", instant=True)

    yield sim_motor_step


@pytest.fixture
async def sim_motor_fly():
    async with DeviceCollector():
        sim_motor_fly = SimThreeAxisStage(name="sim_motor_fly", instant=False)

    yield sim_motor_fly


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
    # should do nothingdocs = defaultdict(list)
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


async def test_stxm_fast_unknown_step(
    andor3: Andor3Ad, sim_motor: ThreeAxisStage, RE: RunEngine
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    step_motor_speed = 1
    set_mock_value(sim_motor.x.velocity, step_motor_speed)

    step_start = 0
    step_end = 2
    plan_time = 10 + step_motor_speed * abs(step_start - step_end)
    count_time = 0.1

    scan_start = -1
    scan_end = 1
    # make the scan motor slow so it can only do 5 steps
    # ideal step-size is 0.2 with speed =2 for 10x10
    set_mock_value(sim_motor.y.max_velocity, 1)

    # Unknown step size
    docs = defaultdict(list)
    RE(
        stxm_fast(
            det=andor3,
            count_time=count_time,
            step_motor=sim_motor.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor.y,
            scan_start=scan_start,
            scan_end=scan_end,
            plan_time=plan_time,
            home=True,
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


async def test_stxm_step_with_home(
    RE: RunEngine, sim_motor_step: SimThreeAxisStage, andor2: Andor2Ad
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    await sim_motor_step.x.set(-1)
    await sim_motor_step.y.set(-2)

    RE(
        stxm_step(
            det=andor2,
            count_time=0.2,
            x_step_motor=sim_motor_step.x,
            x_step_start=0,
            x_step_end=2,
            x_step_size=0.2,
            y_step_motor=sim_motor_step.y,
            y_step_start=-1,
            y_step_end=1,
            y_step_size=0.25,
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
        stream_datum=99,
        event=99,
        stop=1,
    )
    assert -1 == await sim_motor_step.x.user_readback.get_value()
    assert -2 == await sim_motor_step.y.user_readback.get_value()


async def test_stxm_step_without_home(
    RE: RunEngine, sim_motor_step: ThreeAxisStage, andor2: Andor2Ad
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    await sim_motor_step.x.set(-1)
    await sim_motor_step.y.set(-2)
    y_step_end = 1
    x_step_end = 2
    RE(
        stxm_step(
            det=andor2,
            count_time=0.2,
            x_step_motor=sim_motor_step.x,
            x_step_start=0,
            x_step_end=x_step_end,
            x_step_size=0.2,
            y_step_motor=sim_motor_step.y,
            y_step_start=-1,
            y_step_end=y_step_end,
            y_step_size=0.25,
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
        stream_datum=99,
        event=99,
        stop=1,
    )
    assert x_step_end == await sim_motor_step.x.user_readback.get_value()
    assert y_step_end == await sim_motor_step.y.user_readback.get_value()


async def test_stxm_fast_sim_flyable_motor(
    andor2: Andor2Ad, sim_motor_fly: ThreeAxisStage, RE: RunEngine
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    plan_time = 1.5
    count_time = 0.2
    step_size = 0.2
    step_start = -0.5
    step_end = 0.5
    start_monotonic = time.monotonic()
    RE(
        stxm_fast(
            det=andor2,
            count_time=count_time,
            step_motor=sim_motor_fly.x,
            step_start=step_start,
            step_end=step_end,
            scan_motor=sim_motor_fly.y,
            scan_start=1,
            scan_end=2,
            plan_time=plan_time,
            step_size=step_size,
            snake_axes=True,
            home=False,
        ),
        capture_emitted,
    )
    # The overhead is about 3 sec in pytest
    assert time.monotonic() <= start_monotonic + plan_time * 1.1 + 3

    assert docs["event"].__len__() == docs["stream_datum"].__len__()
