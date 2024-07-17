from collections.abc import Sequence
from pathlib import Path

from bluesky.protocols import Hints
from ophyd_async.core import DirectoryProvider, SignalR, StandardDetector
from ophyd_async.core._providers import DirectoryInfo
from ophyd_async.epics.areadetector.drivers import ADBaseShapeProvider
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF

from p99_bluesky.devices.epics.andor2_controller import Andor2Controller
from p99_bluesky.devices.epics.andor3_controller import Andor3Controller
from p99_bluesky.devices.epics.drivers.andor2_driver import Andor2Driver
from p99_bluesky.devices.epics.drivers.andor3_driver import Andor3Driver


class StaticDirectoryProviderPlus:
    """
    Same as DirectoryProvider but add 1 to the file name each time.

    """

    def __init__(
        self,
        directory_path: Path,
        filename_prefix: str = "",
        resource_dir: Path | None = None,
    ):
        self.counter = 0
        if resource_dir is None:
            resource_dir = Path(".")
        self._directory_info = DirectoryInfo(
            root=directory_path,
            resource_dir=resource_dir,
            prefix=filename_prefix,
            suffix="",
        )

    def __call__(self) -> DirectoryInfo:
        self._directory_info.suffix = f"{self.counter}"
        self.counter += 1
        return self._directory_info


class Andor2Ad(StandardDetector):
    _controller: Andor2Controller
    _writer: HDFWriter

    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.drv = Andor2Driver(prefix + "CAM:")
        self.hdf = NDFileHDF(prefix + "HDF5:")
        super().__init__(
            Andor2Controller(self.drv),
            HDFWriter(
                self.hdf,
                directory_provider,
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
    _writer: HDFWriter

    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.drv = Andor3Driver(prefix + "CAM:")
        self.hdf = NDFileHDF(prefix + "HDF5:")
        self.counter = 0

        super().__init__(
            Andor3Controller(self.drv),
            HDFWriter(
                self.hdf,
                directory_provider,
                lambda: self.name,
                ADBaseShapeProvider(self.drv),
                sum="StatsTotal",
                **scalar_sigs,
            ),
            config_sigs=config_sigs,
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints
