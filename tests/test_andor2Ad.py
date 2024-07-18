# from collections import defaultdict
# from pathlib import Path, PosixPath

# import pytest
# from bluesky import plan_stubs as bps
# from bluesky import preprocessors as bpp
# from bluesky.run_engine import RunEngine
# from bluesky.utils import new_uid, short_uid
# from ophyd_async.core import (
#     DetectorTrigger,
#     DeviceCollector,
#     TriggerInfo,
#     assert_emitted,
#     set_mock_value,
# )

# from p99_bluesky.devices.andor2Ad import Andor2Ad, Andor3Ad

# CURRENT_DIRECTORY = "."  # str(Path(__file__).parent)


# def count_mock(det: Andor2Ad | Andor3Ad = andor2, times: int = 1):
#     """Test plan to do the equivalent of bp.count for a mock detector."""

#     yield from bps.stage_all(det)
#     yield from bps.open_run()
#     yield from bps.declare_stream(det, name="primary", collect=False)
#     for _ in range(times):
#         read_value = yield from bps.rd(det._writer.hdf.num_captured)
#         yield from bps.trigger(det, wait=False, group="wait_for_trigger")

#         yield from bps.sleep(0.001)
#         set_mock_value(det._writer.hdf.num_captured, read_value + 1)

#         yield from bps.wait(group="wait_for_trigger")
#         yield from bps.create()
#         yield from bps.read(det)
#         yield from bps.save()

#     yield from bps.close_run()
#     yield from bps.unstage_all(det)


# async def test_Andor(RE: RunEngine, andor2: Andor2Ad):
#     docs = defaultdict(list)

#     def capture_emitted(name, doc):
#         docs[name].append(doc)

#     RE.subscribe(capture_emitted)
#     RE(count_mock(andor2, 2))

#     assert_emitted(
#         docs, start=1, descriptor=1, stream_resource=1, stream_datum=2, event=2, stop=1
#     )
#     docs = defaultdict(list)
#     RE(takeImg(andor2, 0.2, 2, det_trig=DetectorTrigger.internal))
#     # since it is external stream nothing comes back here
#     assert_emitted(docs, start=1, descriptor=1, stop=1)


# async def test_Andor3(RE: RunEngine, andor3: Andor3Ad):
#     docs = defaultdict(list)

#     def capture_emitted(name, doc):
#         docs[name].append(doc)

#     RE.subscribe(capture_emitted)
#     RE(count_mock(andor3))

#     assert_emitted(
#         docs, start=1, descriptor=1, stream_resource=2, stream_datum=2, event=1, stop=1
#     )
#     docs = defaultdict(list)
#     RE(takeImg(andor3, 0.2, 2, det_trig=DetectorTrigger.internal))
#     # since it is external stream nothing comes back here
#     assert_emitted(docs, start=1, descriptor=1, stop=1)


# @pytest.fixture
# def mock_staticDP(
#     dir: Path = Path("/what/dir/"), filename_prefix: str = "p99"
# ) -> StaticDirectoryProviderPlus:
#     mock_staticDP = StaticDirectoryProviderPlus(dir, filename_prefix)
#     return mock_staticDP


# def test_StaticDirectoryProviderPlus():
#     dir: Path = Path("/what/dir/")
#     filename_prefix: str = "p99"
#     mock_staticDP = StaticDirectoryProviderPlus(dir, filename_prefix)
#     assert mock_staticDP.__call__() == DirectoryInfo(
#         root=Path("/what/dir/"), resource_dir=PosixPath("."), prefix="p99", suffix="0"
#     )

#     assert mock_staticDP.__call__() == DirectoryInfo(
#         root=Path("/what/dir/"), resource_dir=PosixPath("."), prefix="p99", suffix="1"
#     )
