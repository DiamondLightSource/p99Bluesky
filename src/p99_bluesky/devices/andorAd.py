from collections.abc import Sequence

from bluesky.protocols import Hints
from ophyd_async.core import PathProvider, SignalR, StandardDetector
from ophyd_async.epics.adcore import ADBaseDatasetDescriber, ADHDFWriter, NDFileHDFIO

from p99_bluesky.devices.epics import Andor2Controller, Andor3Controller
from p99_bluesky.devices.epics.drivers import Andor2DriverIO, Andor3DriverIO


class Andor2Ad(StandardDetector):
    """
    Andor 2 area detector device

    Parameters
    ----------
    prefix: str
        Epic Pv,
    path_provider: PathProvider
        Path provider for hdf writer
    name: str
        Name of the device
    config_sigs: Sequence[SignalR]
        optional config signal to be added
    **scalar_sigs: str
        Optional scalar signals
    """

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
        self.drv = Andor2DriverIO(prefix + "CAM:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        super().__init__(
            Andor2Controller(self.drv),
            ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                ADBaseDatasetDescriber(self.drv),
                # sum="StatsTotal",
                # more="morestuff",
                # **scalar_sigs,
            ),
            config_sigs=[self.drv.acquire_time],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints


class Andor3Ad(StandardDetector):
    """
    Andor 3 area detector device

    """

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
        """Parameters
        ----------
        prefix: str
            Epic Pv,
        path_provider: PathProvider
            Path provider for hdf writer
        name: str
            Name of the device
        config_sigs: Sequence[SignalR]
            optional config signal to be added
        **scalar_sigs: str
            Optional scalar signals
        """
        self.drv = Andor3DriverIO(prefix + "CAM:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        self.counter = 0

        super().__init__(
            Andor3Controller(self.drv),
            ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                ADBaseDatasetDescriber(self.drv),
                # sum="StatsTotal",
                **scalar_sigs,
            ),
            config_sigs=config_sigs,
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints
