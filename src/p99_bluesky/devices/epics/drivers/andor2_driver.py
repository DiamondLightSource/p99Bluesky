from enum import Enum

from ophyd_async.epics.adcore._core_io import ADBaseIO
from ophyd_async.epics.signal import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
)


class TriggerMode(str, Enum):
    internal = "Internal"
    ext_trigger = "External"
    ext_start = "External Start"
    ext_exposure = "External Exposure"
    ext_FVP = "External FVP"
    soft = "Software"


class ImageMode(str, Enum):
    single = "Single"
    multiple = "Multiple"
    continuous = "Continuous"
    fast_kinetics = "Fast Kinetics"


class Andor2Driver(ADBaseIO):
    """
    Epics pv for andor model:DU897_BV as deployed on p99
    """

    def __init__(self, prefix: str) -> None:
        super().__init__(prefix)
        self.trigger_mode = epics_signal_rw(TriggerMode, prefix + "TriggerMode")
        self.accumulate_period = epics_signal_r(
            float, prefix + "AndorAccumulatePeriod_RBV"
        )
        self.image_mode = epics_signal_rw_rbv(ImageMode, prefix + "ImageMode")
        self.stat_mean = epics_signal_r(int, prefix + "STAT:MeanValue_RBV")
