from unittest.mock import patch

import pytest
from ophyd_async.core import (
    DeviceCollector,
    TriggerInfo,
    set_mock_value,
)
from ophyd_async.epics.adcore import ImageMode

from p99_bluesky.devices.epics.andor2_controller import Andor2Controller
from p99_bluesky.devices.epics.drivers.andor2_driver import (
    Andor2DriverIO,
    Andor2TriggerMode,
)


@pytest.fixture
async def Andor(RE) -> Andor2Controller:
    async with DeviceCollector(mock=True):
        drv = Andor2DriverIO("DRIVER:")
        controller = Andor2Controller(drv)

    return controller


async def test_Andor_controller(RE, Andor: Andor2Controller):
    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.prepare(trigger_info=TriggerInfo(number=1, livetime=0.002))
        await Andor.arm()

    driver = Andor._drv

    set_mock_value(driver.accumulate_period, 1)
    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.multiple
    assert await driver.trigger_mode.get_value() == Andor2TriggerMode.internal
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()

    assert await driver.acquire.get_value() is False
