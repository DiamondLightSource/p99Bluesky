import asyncio

from ophyd_async.core import (
    DetectorControl,
    DetectorTrigger,
)
from ophyd_async.core._detector import TriggerInfo
from ophyd_async.epics import adcore
from ophyd_async.epics.adcore import (
    DEFAULT_GOOD_STATES,
    DetectorState,
    stop_busy_record,
)

from p99_bluesky.devices.epics.drivers.andor3_driver import (
    Andor3DriverIO,
    Andor3TriggerMode,
    ImageMode,
)


class Andor3Controller(DetectorControl):
    """
    Andor 3 controller

    """

    _supported_trigger_types = {
        DetectorTrigger.internal: Andor3TriggerMode.internal,
        DetectorTrigger.constant_gate: Andor3TriggerMode.ext_trigger,
        DetectorTrigger.variable_gate: Andor3TriggerMode.ext_exposure,
    }

    def __init__(
        self,
        driver: Andor3DriverIO,
        good_states: set[DetectorState] | None = None,
    ) -> None:
        if good_states is None:
            good_states = set(DEFAULT_GOOD_STATES)
        self._drv = driver
        self.good_states = good_states

    def get_deadtime(self, exposure: float | None) -> float:
        if exposure is None:
            return 0.1
        return exposure + 0.1

    async def prepare(self, trigger_info: TriggerInfo):
        if trigger_info.livetime is not None:
            await adcore.set_exposure_time_and_acquire_period_if_supplied(
                self, self._drv, trigger_info.livetime
            )
        await asyncio.gather(
            self._drv.trigger_mode.set(self._get_trigger_mode(trigger_info.trigger)),
            self._drv.num_images.set(
                999_999 if trigger_info.number == 0 else trigger_info.number
            ),
            self._drv.image_mode.set(ImageMode.fixed),
        )

    async def arm(self) -> None:
        # Standard arm the detector and wait for the acquire PV to be True
        self._arm_status = await adcore.start_acquiring_driver_and_ensure_status(
            self._drv
        )

    async def wait_for_idle(self):
        if self._arm_status:
            await self._arm_status

    @classmethod
    def _get_trigger_mode(cls, trigger: DetectorTrigger) -> Andor3TriggerMode:
        if trigger not in cls._supported_trigger_types.keys():
            raise ValueError(
                f"{cls.__name__} only supports the following trigger "
                f"types: {cls._supported_trigger_types.keys()} but was asked to "
                f"use {trigger}"
            )
        return cls._supported_trigger_types[trigger]

    async def disarm(self):
        await stop_busy_record(self._drv.acquire, False, timeout=1)
