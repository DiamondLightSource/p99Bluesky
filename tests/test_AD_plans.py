from collections import defaultdict

from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    StaticPathProvider,
    assert_emitted,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.areadetector.drivers.ad_base import DetectorState

from p99_bluesky.devices.andorAd import Andor2Ad, Andor3Ad
from p99_bluesky.devices.stages import ThreeAxisStage
from p99_bluesky.plans.ad_plans import takeImg, tiggerImg


async def test_Andor2_tiggerImg(
    RE: RunEngine, andor2: Andor2Ad, static_path_provider: StaticPathProvider
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE.subscribe(capture_emitted)

    set_mock_value(andor2.drv.detector_state, DetectorState.Idle)

    RE(tiggerImg(andor2, 4))

    assert (
        str(static_path_provider._directory_path)
        == await andor2.hdf.file_path.get_value()
    )
    assert (
        str(static_path_provider._directory_path) + "/test-andor2-hdf0"
        == await andor2.hdf.full_file_name.get_value()
    )
    assert_emitted(
        docs, start=1, descriptor=1, stream_resource=1, stream_datum=1, event=1, stop=1
    )


async def test_Andor2_takeImg(
    RE: RunEngine, andor2: Andor2Ad, static_path_provider: StaticPathProvider
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE.subscribe(capture_emitted)

    set_mock_value(andor2.drv.detector_state, DetectorState.Idle)
    # jumping index to 5 as if it taken 5 images.
    callback_on_mock_put(
        andor2.drv.acquire,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.num_captured, 5),
    )

    RE(takeImg(andor2, 1, 4))
    assert (
        str(static_path_provider._directory_path)
        == await andor2.hdf.file_path.get_value()
    )
    assert (
        str(static_path_provider._directory_path) + "/test-andor2-hdf0"
        == await andor2.hdf.full_file_name.get_value()
    )
    assert_emitted(docs, start=1, descriptor=1, stream_resource=1, stream_datum=1, stop=1)


async def test_Andor2_scan(
    RE: RunEngine,
    andor2: Andor2Ad,
    static_path_provider: StaticPathProvider,
    sim_motor: ThreeAxisStage,
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE.subscribe(capture_emitted)
    set_mock_value(andor2.drv.detector_state, DetectorState.Idle)
    RE(scan([andor2], sim_motor.y, -3, 3, 10))
    assert (
        str(static_path_provider._directory_path)
        == await andor2.hdf.file_path.get_value()
    )
    assert (
        str(static_path_provider._directory_path) + "/test-andor2-hdf0"
        == await andor2.hdf.full_file_name.get_value()
    )
    assert_emitted(
        docs, start=1, descriptor=1, stream_resource=1, stream_datum=10, event=10, stop=1
    )


async def test_Andor3_scan(
    RE: RunEngine,
    andor3: Andor3Ad,
    static_path_provider: StaticPathProvider,
    sim_motor: ThreeAxisStage,
):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE.subscribe(capture_emitted)
    set_mock_value(andor3.drv.detector_state, DetectorState.Idle)
    RE(scan([andor3], sim_motor.x, -3, 3, 10))
    assert (
        str(static_path_provider._directory_path)
        == await andor3.hdf.file_path.get_value()
    )
    assert (
        str(static_path_provider._directory_path) + "/test-andor3-hdf0"
        == await andor3.hdf.full_file_name.get_value()
    )
    assert_emitted(
        docs, start=1, descriptor=1, stream_resource=1, stream_datum=10, event=10, stop=1
    )
