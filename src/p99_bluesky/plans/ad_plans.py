from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.utils import Msg, short_uid
from ophyd_async.core import DetectorTrigger, TriggerInfo

from p99_bluesky.devices.andor2Ad import Andor2Ad, Andor3Ad


def takeImg(
    det: Andor2Ad | Andor3Ad,
    exposure: float,
    n_img: int = 1,
    det_trig: DetectorTrigger = DetectorTrigger.internal,
):
    """
    Bare minimum to take an image using prepare plan with full detector control
    e.g. Able to change tigger_info unlike tigger
    """
    grp = short_uid("prepare")
    deadtime: float = det.controller.get_deadtime(exposure)
    tigger_info = TriggerInfo(n_img, det_trig, deadtime, exposure)

    @bpp.stage_decorator([det])
    @bpp.run_decorator()
    def innerTakeImg():
        # yield from bps.create(name="primary")
        yield from bps.declare_stream(det, name="primary")

        yield from bps.prepare(det, tigger_info, group=grp, wait=True)
        yield from bps.kickoff(det, group=grp, wait=True)

        yield from bps.collect(det, name="primary", return_payload=True)
        yield from bps.complete(det, group=grp, wait=True)

    return (yield from innerTakeImg())


def tiggerImg(dets: Andor2Ad | Andor3Ad, value: int):
    yield Msg("set", dets.drv.acquire_time, value)

    @bpp.stage_decorator([dets])
    @bpp.run_decorator()
    def innerTiggerImg():
        return (yield from bps.trigger_and_read([dets]))

    return (yield from innerTiggerImg())
