from blueapi.core import MsgGenerator
from bluesky import plan_stubs as bps
from bluesky import preprocessors as bpp
from bluesky.utils import Msg, short_uid
from ophyd_async.core import DetectorTrigger, TriggerInfo

from p99_bluesky.devices.andorAd import Andor2Ad, Andor3Ad


def takeImg(
    det: Andor2Ad | Andor3Ad,
    exposure: float,
    n_img: int = 1,
    det_trig: DetectorTrigger = DetectorTrigger.internal,
) -> MsgGenerator:
    """
    Bare minimum to take an image using prepare plan with full detector control
    e.g. Able to change tigger_info unlike tigger
    """
    grp = short_uid("prepare")
    deadtime: float = det.controller.get_deadtime(exposure)
    tigger_info = TriggerInfo(
        number=n_img,
        trigger=det_trig,
        deadtime=deadtime,
        livetime=exposure,
        frame_timeout=None,
    )

    @bpp.stage_decorator([det])
    @bpp.run_decorator()
    def innerTakeImg():
        yield from bps.prepare(det, tigger_info, group=grp, wait=True)
        yield from bps.trigger_and_read([det])

    yield from innerTakeImg()


def tiggerImg(dets: Andor2Ad | Andor3Ad, value: int) -> MsgGenerator:
    yield Msg("set", dets.drv.acquire_time, value)

    @bpp.stage_decorator([dets])
    @bpp.run_decorator()
    def innerTiggerImg():
        return (yield from bps.trigger_and_read([dets]))

    yield from innerTiggerImg()
