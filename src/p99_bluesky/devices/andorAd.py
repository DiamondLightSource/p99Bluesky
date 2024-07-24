from collections.abc import Sequence

from bluesky.protocols import Hints
from ophyd_async.core import PathProvider, SignalR, StandardDetector
from ophyd_async.epics.adcore import ADBaseShapeProvider, ADHDFWriter, NDFileHDFIO

from p99_bluesky.devices.epics.andor2_controller import Andor2Controller
from p99_bluesky.devices.epics.andor3_controller import Andor3Controller
from p99_bluesky.devices.epics.drivers.andor2_driver import Andor2Driver
from p99_bluesky.devices.epics.drivers.andor3_driver import Andor3Driver


class Andor2Ad(StandardDetector):
    _controller: Andor2Controller
    _writer: ADHDFWriter

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.drv = Andor2Driver(prefix + "CAM:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        super().__init__(
            Andor2Controller(self.drv),
            ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                ADBaseShapeProvider(self.drv),
                # sum="StatsTotal",
                # more="morestuff",
                **scalar_sigs,
            ),
            config_sigs=[self.drv.acquire_time, self.drv.stat_mean],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints


class Andor3Ad(StandardDetector):
    _controller: Andor3Controller
    _writer: ADHDFWriter

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.drv = Andor3Driver(prefix + "CAM:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        self.counter = 0

        super().__init__(
            Andor3Controller(self.drv),
            ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                ADBaseShapeProvider(self.drv),
                # sum="StatsTotal",
                **scalar_sigs,
            ),
            config_sigs=config_sigs,
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints
