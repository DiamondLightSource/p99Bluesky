from enum import Enum

from ophyd_async.epics.adcore._core_io import ADBaseIO
from ophyd_async.epics.signal import epics_signal_rw, epics_signal_rw_rbv


class Andor3TriggerMode(str, Enum):
    internal = "Internal"
    ext_start = "External Start"
    ext_exposure = "External Exposure"
    soft = "Software"
    ext_trigger = "External"


class ImageMode(str, Enum):
    fixed = "Fixed"
    continuous = "Continuous"


class Andor3DriverIO(ADBaseIO):
    """
    Epics pv for andor model:ZYLA-5.5-cl3 as deployed on p99
    """

    def __init__(self, prefix: str) -> None:
        super().__init__(prefix)
        self.trigger_mode = epics_signal_rw(Andor3TriggerMode, prefix + "TriggerMode")
        self.image_mode = epics_signal_rw_rbv(ImageMode, prefix + "ImageMode")
