import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, set_mock_value
from ophyd_async.epics.motor import Motor

from p99_bluesky.plan_stubs.motor_plan import check_within_limit


@pytest.fixture
async def mock_motor():
    async with DeviceCollector(mock=True):
        mock_motor = Motor("BLxx-MO-xx-01:", "mock_motor")
    yield mock_motor


def test_check_within_limit(mock_motor: Motor, RE: RunEngine):
    set_mock_value(mock_motor.low_limit_travel, -10)
    set_mock_value(mock_motor.high_limit_travel, 20)

    with pytest.raises(ValueError):
        RE(check_within_limit([-11], mock_motor))

    with pytest.raises(ValueError):
        RE(check_within_limit([21], mock_motor))

    RE(check_within_limit([18], mock_motor))
