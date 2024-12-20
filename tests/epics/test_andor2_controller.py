from unittest.mock import patch

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    DeviceCollector,
    TriggerInfo,
)
from ophyd_async.epics.adcore import ImageMode
from ophyd_async.testing import set_mock_value

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
        await Andor.prepare(
            trigger_info=TriggerInfo(number_of_triggers=1, livetime=0.002)
        )
        await Andor.arm()

    driver = Andor._drv

    set_mock_value(driver.accumulate_period, 1)
    assert await driver.num_images.get_value() == 1
    assert await driver.image_mode.get_value() == ImageMode.MULTIPLE
    assert await driver.trigger_mode.get_value() == Andor2TriggerMode.INTERNAL
    assert await driver.acquire.get_value() is True
    assert await driver.acquire_time.get_value() == 0.002
    assert Andor.get_deadtime(2) == 2 + 0.1
    assert Andor.get_deadtime(None) == 0.1

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()

    assert await driver.acquire.get_value() is False

    with patch("ophyd_async.core.wait_for_value", return_value=None):
        await Andor.disarm()
    with pytest.raises(ValueError):
        Andor._get_trigger_mode(DetectorTrigger.EDGE_TRIGGER)

    assert await driver.acquire.get_value() is False
