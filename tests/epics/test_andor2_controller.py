from unittest.mock import patch

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    DeviceCollector,
    set_mock_value,
)
from ophyd_async.epics.adcore import ImageMode

from p99_bluesky.devices.epics.andor2_controller import Andor2Controller
from p99_bluesky.devices.epics.drivers.andor2_driver import Andor2Driver, TriggerMode


@pytest.fixture
async def Andor(RE) -> Andor2Controller:
    async with DeviceCollector(mock=True):
        drv = Andor2Driver("DRIVER:")
        controller = Andor2Controller(drv)

    return controller


async def test_Andor_controller(RE, Andor: Andor2Controller):
    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.arm(num=1, exposure=0.002, trigger=DetectorTrigger.internal)

    driver = Andor.driver

    set_mock_value(driver.accumulate_period, 1)
    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()

    assert await driver.acquire.get_value() is False
