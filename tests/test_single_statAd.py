from unittest.mock import Mock

import pytest
from ophyd_async.core import (
    DeviceCollector,
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.areadetector.drivers.ad_base import DetectorState

from p99_bluesky.devices.andor2Ad import Andor2Ad, StaticDirectoryProviderPlus


@pytest.fixture
async def andor2(tmp_path) -> Andor2Ad:
    dp = StaticDirectoryProviderPlus(tmp_path, "test-")
    async with DeviceCollector(mock=True):
        andor2 = Andor2Ad("TEST", dp, "andor2")

    set_mock_value(andor2._controller.driver.array_size_x, 10)
    set_mock_value(andor2._controller.driver.array_size_y, 20)
    set_mock_value(andor2.hdf.file_path_exists, True)
    set_mock_value(andor2.hdf.num_captured, 0)
    set_mock_value(andor2.hdf.file_path, str(tmp_path))
    set_mock_value(andor2.hdf.full_file_name, str(tmp_path) + "/test-andor2-hdf0")
    set_mock_value(andor2.drv.detector_state, DetectorState.Idle)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(0, 100)
    callback_on_mock_put(
        andor2._writer.hdf.capture,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.capture, value=True),
    )
    callback_on_mock_put(
        andor2.drv.acquire,
        lambda *_, **__: set_mock_value(andor2._writer.hdf.num_captured, rbv_mocks.get()),
    )
    return andor2


"""
@pytest.fixture
async def single_trigger_stat_det(andor2: Andor2Ad):
    async with DeviceCollector(mock=True):
        stats = NDPluginStats("PREFIX:STATS")
        det = SingleTriggerDet(
            drv=andor2.drv, stats=stats, read_uncached=[andor2.drv.stat_mean]
        )

    assert det.name == "det"
    assert stats.name == "det-stats"
    yield det


async def test_single_stat_ad(single_trigger_stat_det: SingleTriggerDet, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    num_cnt = 10

    mean_mocks = Mock()
    mean_mocks.get.side_effect = range(0, 100, 2)
    callback_on_mock_put(
        single_trigger_stat_det.drv.acquire,
        lambda *_, **__: set_mock_value(
            single_trigger_stat_det.drv.stat_mean, mean_mocks.get()
        ),
    )

    RE(bp.count([single_trigger_stat_det], num_cnt), capture_emitted)

    drv = single_trigger_stat_det.drv
    assert 1 == await drv.acquire.get_value()
    assert ImageMode.single == await drv.image_mode.get_value()
    assert True is await drv.wait_for_plugins.get_value()

    assert_emitted(docs, start=1, descriptor=1, event=num_cnt, stop=1)
    assert (
        docs["descriptor"][0]["configuration"]["det"]["data"]["det-drv-acquire_time"] == 0
    )
    assert docs["event"][0]["data"]["det-drv-array_counter"] == 0

    for i, mean in enumerate(range(0, num_cnt, 2)):
        assert docs["event"][i]["data"]["det-drv-stat_mean"] == mean
"""
