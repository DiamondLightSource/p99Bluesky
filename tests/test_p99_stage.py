import pytest
from ophyd_async.core import DeviceCollector
from ophyd_async.testing import set_mock_value

from p99_bluesky.devices.p99.sample_stage import (
    FilterMotor,
    SampleAngleStage,
    p99StageSelections,
)

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001


@pytest.fixture
async def mock_sampleAngleStage():
    async with DeviceCollector(mock=True):
        mock_sampleAngleStage = SampleAngleStage(
            "p99-MO-TABLE-01:", name="mock_sampleAngleStage"
        )
    yield mock_sampleAngleStage


@pytest.fixture
async def mock_filter_wheel():
    async with DeviceCollector(mock=True):
        mock_filter_wheel = FilterMotor("p99-MO-TABLE-01:", name="mock_filter_wheel")
    yield mock_filter_wheel


async def test_sampleAngleStage(mock_sampleAngleStage: SampleAngleStage) -> None:
    assert mock_sampleAngleStage.name == "mock_sampleAngleStage"
    assert mock_sampleAngleStage.theta.name == "mock_sampleAngleStage-theta"
    assert mock_sampleAngleStage.roll.name == "mock_sampleAngleStage-roll"
    assert mock_sampleAngleStage.pitch.name == "mock_sampleAngleStage-pitch"


async def test_filter_wheel(mock_filter_wheel: FilterMotor) -> None:
    assert mock_filter_wheel.name == "mock_filter_wheel"
    set_mock_value(mock_filter_wheel.user_setpoint, p99StageSelections.CD25UM)
    assert await mock_filter_wheel.user_setpoint.get_value() == p99StageSelections.CD25UM
