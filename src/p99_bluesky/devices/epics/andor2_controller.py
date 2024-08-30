import asyncio

from ophyd_async.core import AsyncStatus, DetectorControl, DetectorTrigger
from ophyd_async.epics.adcore import (
    DEFAULT_GOOD_STATES,
    DetectorState,
    start_acquiring_driver_and_ensure_status,
    stop_busy_record,
)

from p99_bluesky.devices.epics.drivers.andor2_driver import (
    Andor2Driver,
    ImageMode,
    TriggerMode,
)

TRIGGER_MODE = {
    DetectorTrigger.internal: TriggerMode.internal,
    DetectorTrigger.constant_gate: TriggerMode.ext_trigger,
    DetectorTrigger.variable_gate: TriggerMode.ext_trigger,
}


class Andor2Controller(DetectorControl):
    """
    Andor 2 controller

    """

    def __init__(
        self,
        driver: Andor2Driver,
        good_states: set[DetectorState] | None = None,
    ) -> None:
        if good_states is None:
            good_states = set(DEFAULT_GOOD_STATES)
        self.driver = driver
        self.good_states = good_states

    def get_deadtime(self, exposure: float) -> float:
        return exposure + 0.2

    async def arm(
        self,
        num: int = 1,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        exposure: float | None = None,
    ) -> AsyncStatus:
        funcs = [
            self.driver.num_images.set(999_999 if num == 0 else num),
            self.driver.image_mode.set(ImageMode.multiple),
            self.driver.trigger_mode.set(TRIGGER_MODE[trigger]),
        ]
        if exposure is not None:
            funcs.append(self.driver.acquire_time.set(exposure))

        await asyncio.gather(*funcs)
        return await start_acquiring_driver_and_ensure_status(
            self.driver, good_states=self.good_states
        )

    async def disarm(self):
        await stop_busy_record(self.driver.acquire, False, timeout=1)
