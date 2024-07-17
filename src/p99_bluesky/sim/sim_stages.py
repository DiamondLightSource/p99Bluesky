from ophyd_async.core import Device
from ophyd_async.core.signal import (
    soft_signal_rw,
)
from ophyd_async.sim.demo.sim_motor import SimMotor


class p99SimMotor(SimMotor):
    def __init__(self, name="", instant=True) -> None:
        self.max_velocity = soft_signal_rw(float, 10000)
        self.acceleration_time = soft_signal_rw(float, 0.1)
        self.precision = soft_signal_rw(int, 3)
        self.deadband = soft_signal_rw(float, 0.05)
        self.motor_done_move = soft_signal_rw(int, 1)
        self.low_limit_travel = soft_signal_rw(float, -10)
        self.high_limit_travel = soft_signal_rw(float, 10)
        super().__init__(name=name, instant=instant)


class SimThreeAxisStage(Device):
    def __init__(self, name: str, infix: list[str] | None = None, instant=False):
        if infix is None:
            infix = ["X", "Y", "Z"]
        self.x = p99SimMotor(name + infix[0], instant=instant)
        self.y = p99SimMotor(name + infix[1], instant=instant)
        self.z = p99SimMotor(name + infix[2], instant=instant)
        super().__init__(name=name)
