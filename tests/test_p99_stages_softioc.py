import asyncio
from collections import defaultdict

from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector, assert_emitted

from p99_bluesky.devices.p99.sample_stage import (
    FilterMotor,
    SampleAngleStage,
    p99StageSelections,
)

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.5


async def test_fake_p99(RE: RunEngine, xyz_motor) -> None:
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    await asyncio.sleep(A_BIT)
    with DeviceCollector(mock=False):
        mock_sampleAngleStage = SampleAngleStage(
            "p99-MO-TABLE-01:", name="mock_sampleAngleStage"
        )
        mock_filter_wheel = FilterMotor(
            "p99-MO-STAGE-02:MP:SELECT", name="mock_filter_wheel"
        )

    assert mock_sampleAngleStage.roll.name == "mock_sampleAngleStage-roll"
    assert mock_sampleAngleStage.pitch.name == "mock_sampleAngleStage-pitch"
    assert mock_filter_wheel.user_setpoint.name == "mock_filter_wheel-user_setpoint"

    await asyncio.gather(
        mock_sampleAngleStage.theta.set(2),
        mock_sampleAngleStage.pitch.set(3.1),
        mock_sampleAngleStage.roll.set(4),
        mock_filter_wheel.user_setpoint.set(p99StageSelections.Cd25um),
    )
    await asyncio.sleep(A_BIT)
    result = asyncio.gather(
        mock_sampleAngleStage.theta.get_value(),
        mock_sampleAngleStage.pitch.get_value(),
        mock_sampleAngleStage.roll.get_value(),
        mock_filter_wheel.user_setpoint.get_value(),
    )
    await asyncio.wait_for(result, timeout=2)
    assert result.result() == [2.0, 3.1, 4.0, p99StageSelections.Cd25um]

    RE(
        scan(
            [mock_sampleAngleStage.theta],
            xyz_motor.z,
            -3,
            3,
            10,
        ),
        [
            capture_emitted,
        ],
    )
    assert_emitted(docs, start=1, descriptor=1, event=10, stop=1)
    await asyncio.sleep(A_BIT)
