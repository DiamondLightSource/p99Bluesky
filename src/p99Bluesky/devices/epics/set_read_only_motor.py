import asyncio
import time
from collections.abc import Callable

from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class SetReadOnlyMotor(StandardReadable, Movable):
    """Device that moves a motor with only setpoint and readback.
    Parameters
    ----------
    prefix:
        EPICS PV (None common part up to and including :).
    name:
        Name for the motor.
    suffix:
        Th last part of any EPICS PV, default is the [".VAL", ".RBV"].
    Notes
    -----
    Example usage::
        stage = NoConfigMotor("prefix", "name", "suffix")
    """

    def __init__(self, prefix: str, name="", suffix: list[str] | None = None) -> None:
        # Define some signals
        if suffix is None:
            suffix = [".VAL", ".RBV"]
        self.setpoint = epics_signal_rw(float, prefix + suffix[0])
        self.readback = epics_signal_r(float, prefix + suffix[1])
        self.units = epics_signal_r(str, prefix + ".EGU")
        # Whether set() should complete successfully or not
        self._set_success = True
        # Set name and signals for read() and read_configuration()
        self.set_readable_signals(
            read=[self.readback],
            config=[self.units],
        )
        super().__init__(name=name)

    def set_name(self, name: str):
        super().set_name(name)
        # Readback should be named the same as its parent in read()
        self.readback.set_name(name)

    async def _move(self, new_position: float, watchers: list[Callable] | None = None):
        if watchers is None:
            watchers = []
        self._set_success = True
        start = time.monotonic()
        old_position = await asyncio.gather(
            self.setpoint.get_value(),
        )

        def update_watchers(current_position: float):
            for watcher in watchers:
                watcher(
                    name=self.name,
                    current=current_position,
                    initial=old_position,
                    target=new_position,
                    time_elapsed=time.monotonic() - start,
                )

        self.readback.subscribe_value(update_watchers)
        try:
            await self.setpoint.set(new_position)
        finally:
            self.readback.clear_sub(update_watchers)
        if not self._set_success:
            raise RuntimeError("Motor was stopped")

    def move(self, new_position: float, timeout: float | None = None):
        """Commandline only synchronous move of a Motor"""
        from bluesky.run_engine import call_in_bluesky_event_loop, in_bluesky_event_loop

        if in_bluesky_event_loop():
            raise RuntimeError("Will deadlock run engine if run in a plan")
        call_in_bluesky_event_loop(self._move(new_position), timeout)  # type: ignore

    def set(self, value: float, timeout: float | None = None) -> AsyncStatus:
        watchers: list[Callable] = []
        coro = asyncio.wait_for(self._move(value, watchers), timeout=timeout)
        return AsyncStatus(coro, watchers)
