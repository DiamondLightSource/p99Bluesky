from collections import defaultdict
from unittest import mock

import pytest
from bluesky.run_engine import RunEngine
from numpy import linspace
from ophyd.sim import SynPeriodicSignal
from ophyd_async.core import (
    assert_emitted,
    get_mock_put,
)

from p99_bluesky.devices.stages import ThreeAxisStage
from p99_bluesky.plans.fast_scan import fast_scan_1d, fast_scan_grid

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001


@pytest.fixture
def det():
    return SynPeriodicSignal(name="rand", labels={"detectors"})


async def test_fast_scan_1d_fail_limit_check(
    sim_motor: ThreeAxisStage, RE: RunEngine, det
):
    """Testing both high and low limits making sure nothing get run if it is exceeded"""
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    with pytest.raises(ValueError):
        RE(fast_scan_1d([det], sim_motor.x, 8, 20, 10), capture_emitted)

    with pytest.raises(ValueError):
        RE(fast_scan_1d([det], sim_motor.x, -208, 0, 10), capture_emitted)

    assert 0 == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 0 == get_mock_put(sim_motor.x.velocity).call_count
    assert_emitted(docs, start=2, stop=2)


async def test_fast_scan_1d_success(sim_motor: ThreeAxisStage, RE: RunEngine, det):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(fast_scan_1d([det], sim_motor.x, 5, -1, 8.0), capture_emitted)

    assert 2.78 == await sim_motor.x.velocity.get_value()
    assert 2 == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 3 == get_mock_put(sim_motor.x.velocity).call_count
    # check speed is set and reset
    assert [
        mock.call(10.0, wait=True, timeout=mock.ANY),  # prepare set it to max speed
        mock.call(8.0, wait=True, timeout=mock.ANY),
        mock.call(2.78, wait=True, timeout=mock.ANY),
    ] == get_mock_put(sim_motor.x.velocity).call_args_list

    """Only 1 event as sim motor motor_done_move is set to true,
      so only 1 loop is ran"""
    assert_emitted(docs, start=1, descriptor=1, event=1, stop=1)


async def test_fast_scan_1d_success_without_speed(
    sim_motor: ThreeAxisStage, RE: RunEngine, det
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(fast_scan_1d([det], sim_motor.x, 5, -1), capture_emitted)

    assert 2.78 == await sim_motor.x.velocity.get_value()
    assert 2 == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 3 == get_mock_put(sim_motor.x.velocity).call_count
    # check speed is set and reset
    assert [
        mock.call(pytest.approx(10.0), wait=True, timeout=mock.ANY),
        mock.call(pytest.approx(2.78), wait=True, timeout=mock.ANY),
        mock.call(pytest.approx(2.78), wait=True, timeout=mock.ANY),
    ] == get_mock_put(sim_motor.x.velocity).call_args_list

    """Only 1 event as sim motor motor_done_move is set to true,
      so only 1 loop is ran"""
    assert_emitted(docs, start=1, descriptor=1, event=1, stop=1)


async def test_fast_scan_2d_success(sim_motor: ThreeAxisStage, RE: RunEngine, det):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    x_start = 0
    x_end = 2
    num_step = 5
    y_start = -5
    y_end = 5
    speed = 1
    snake_axes = False
    RE(
        fast_scan_grid(
            [det],
            sim_motor.x,
            x_start,
            x_end,
            num_step,
            sim_motor.y,
            y_start,
            y_end,
            speed,
            snake_axes=snake_axes,
        ),
        capture_emitted,
    )

    assert 2.78 == await sim_motor.x.velocity.get_value()
    assert num_step == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 0 == get_mock_put(sim_motor.x.velocity).call_count
    # check step set points
    steps = linspace(x_start, x_end, num_step, endpoint=True)
    for cnt, motor_x in enumerate(get_mock_put(sim_motor.x.user_setpoint).call_args_list):
        assert motor_x == mock.call(steps[cnt], wait=True, timeout=mock.ANY)

    assert 2.88 == await sim_motor.y.velocity.get_value()
    assert num_step * 3 == get_mock_put(sim_motor.y.velocity).call_count
    assert num_step * 2 == get_mock_put(sim_motor.y.user_setpoint).call_count
    # check scan axis set and end point
    for cnt, motor_y in enumerate(get_mock_put(sim_motor.y.user_setpoint).call_args_list):
        if cnt % 2 == 0:
            assert motor_y == mock.call(y_start, wait=True, timeout=mock.ANY)
        else:
            assert motor_y == mock.call(y_end, wait=True, timeout=mock.ANY)
    """Only 1 event per step as sim motor motor_done_move is set to true,
      so only 1 loop is ran"""
    assert_emitted(docs, start=1, descriptor=1, event=num_step, stop=1)


async def test_fast_scan_2d_Snake_success(sim_motor: ThreeAxisStage, RE: RunEngine, det):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    x_start = 0
    x_end = 2
    num_step = 5
    y_start = -5
    y_end = 4
    speed = 1
    snake_axes = True
    RE(
        fast_scan_grid(
            [det],
            sim_motor.x,
            x_start,
            x_end,
            num_step,
            sim_motor.y,
            y_start,
            y_end,
            speed,
            snake_axes=snake_axes,
        ),
        capture_emitted,
    )

    assert 2.78 == await sim_motor.x.velocity.get_value()
    assert num_step == get_mock_put(sim_motor.x.user_setpoint).call_count
    assert 0 == get_mock_put(sim_motor.x.velocity).call_count
    steps = linspace(x_start, x_end, num_step, endpoint=True)
    for cnt, motor_x in enumerate(get_mock_put(sim_motor.x.user_setpoint).call_args_list):
        assert motor_x == mock.call(steps[cnt], wait=True, timeout=mock.ANY)

    assert 2.88 == await sim_motor.y.velocity.get_value()
    assert num_step * 3 == get_mock_put(sim_motor.y.velocity).call_count
    assert num_step * 2 == get_mock_put(sim_motor.y.user_setpoint).call_count
    """ build a list of expected scan motor position"""
    y_position = [y_start]
    for cnt in range(0, num_step):
        if cnt % 2 == 0:
            y_position.extend((y_end, y_end))
        else:
            y_position.extend((y_start, y_start))
    if num_step % 2 == 0:
        y_position.append(y_start)
    else:
        y_position.append(y_end)
    """check them"""
    for cnt, motor_y in enumerate(get_mock_put(sim_motor.y.user_setpoint).call_args_list):
        assert motor_y == mock.call(y_position[cnt], wait=True, timeout=mock.ANY)

    """Only 1 event per step as sim motor motor_done_move is set to true,
      so only 1 loop is ran"""
    assert_emitted(docs, start=1, descriptor=1, event=num_step, stop=1)
