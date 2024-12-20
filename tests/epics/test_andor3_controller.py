from unittest.mock import patch

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    DeviceCollector,
    TriggerInfo,
)

from p99_bluesky.devices.epics.andor3_controller import Andor3Controller
from p99_bluesky.devices.epics.drivers.andor3_driver import (
    Andor3DriverIO,
    Andor3TriggerMode,
    ImageMode,
)


@pytest.fixture
async def Andor(RE) -> Andor3Controller:
    async with DeviceCollector(mock=True):
        drv = Andor3DriverIO("DRIVER:")
        controller = Andor3Controller(drv)

    return controller


async def test_Andor3_controller(RE, Andor: Andor3Controller):
    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.prepare(
            trigger_info=TriggerInfo(number_of_triggers=1, livetime=0.002)
        )
        await Andor.arm()

    driver = Andor._drv

    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.FIXED
    assert await driver.trigger_mode.get_value() == Andor3TriggerMode.INTERNAL
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002
    assert Andor.get_deadtime(2) == 2 + 0.1
    assert Andor.get_deadtime(None) == 0.1

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()
    with pytest.raises(ValueError):
        Andor._get_trigger_mode(DetectorTrigger.EDGE_TRIGGER)

    assert await driver.acquire.get_value() is False
