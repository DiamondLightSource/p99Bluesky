from ophyd_async.core import StrictEnum
from ophyd_async.epics.adcore._core_io import ADBaseIO
from ophyd_async.epics.core import epics_signal_rw, epics_signal_rw_rbv


class Andor3TriggerMode(StrictEnum):
    INTERNAL = "Internal"
    EXT_START = "External Start"
    EXT_EXPOSURE = "External Exposure"
    SOFT = "Software"
    EXT_TRIGGER = "External"


class ImageMode(StrictEnum):
    FIXED = "Fixed"
    CONTINUOUS = "Continuous"


class Andor3DriverIO(ADBaseIO):
    """
    Epics pv for andor model:ZYLA-5.5-cl3 as deployed on p99
    """

    def __init__(self, prefix: str) -> None:
        super().__init__(prefix)
        self.trigger_mode = epics_signal_rw(Andor3TriggerMode, prefix + "TriggerMode")
        self.image_mode = epics_signal_rw_rbv(ImageMode, prefix + "ImageMode")
