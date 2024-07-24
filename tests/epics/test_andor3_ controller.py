from unittest.mock import patch

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    DeviceCollector,
)

from p99_bluesky.devices.epics.andor3_controller import Andor3Controller
from p99_bluesky.devices.epics.drivers.andor3_driver import (
    Andor3Driver,
    ImageMode,
    TriggerMode,
)


@pytest.fixture
async def Andor(RE) -> Andor3Controller:
    async with DeviceCollector(mock=True):
        drv = Andor3Driver("DRIVER:")
        controller = Andor3Controller(drv)

    return controller


async def test_Andor3_controller(RE, Andor: Andor3Controller):
    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.arm(num=1, exposure=0.002, trigger=DetectorTrigger.internal)

    driver = Andor.driver

    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.fixed
    assert await driver.trigger_mode.get_value() == TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002
    assert Andor.get_deadtime(2) == 2 + 0.2

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()

    assert await driver.acquire.get_value() is False
