from ophyd_async.core import Device, StrictEnum
from ophyd_async.epics.core import epics_signal_rw


class SampleAngleStage(Device):
    def __init__(self, prefix: str, name: str):
        self.theta = epics_signal_rw(
            float, prefix + "WRITETHETA:RBV", prefix + "WRITETHETA"
        )
        self.roll = epics_signal_rw(float, prefix + "WRITEROLL:RBV", prefix + "WRITEROLL")
        self.pitch = epics_signal_rw(
            float, prefix + "WRITEPITCH:RBV", prefix + "WRITEPITCH"
        )
        super().__init__(name=name)


class p99StageSelections(StrictEnum):
    EMPTY = "EMPTY"
    MN5UM = "MN 5UM"
    FE = "FE (EMPTY)"
    CO5UM = "CO 5UM"
    NI5UM = "NI 5UM"
    CU5UM = "CU 5UM"
    ZN5UM = "ZN 5UM"
    ZR = "ZR (EMPTY)"
    MO = "MO (EMPTY)"
    RH = "RH (EMPTY)"
    PD = "PD (EMPTY)"
    AG = "AG (EMPTY)"
    CD25UM = "CD 25UM"
    W = "W (EMPTY)"
    PT = "PT (EMPTY)"
    USER = "USER"


class FilterMotor(Device):
    def __init__(self, prefix: str, name: str):
        self.user_setpoint = epics_signal_rw(p99StageSelections, prefix)
        super().__init__(name=name)
