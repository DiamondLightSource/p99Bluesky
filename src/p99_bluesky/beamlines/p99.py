from pathlib import Path

from dodal.common.beamlines.beamline_utils import (
    device_instantiation,
    get_path_provider,
    set_path_provider,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.common.visit import StaticVisitPathProvider
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name

from p99_bluesky.devices import Andor2Ad
from p99_bluesky.devices.p99.sample_stage import FilterMotor, SampleAngleStage
from p99_bluesky.devices.stages import ThreeAxisStage

BL = get_beamline_name("P99")
set_log_beamline(BL)
set_utils_beamline(BL)

set_path_provider(
    StaticVisitPathProvider(
        BL,
        Path(
            "/dls/p99/data/2024/cm37284-2/processing/writenData"
        ),  # latest commissioning visit
    )
)


def sample_angle_stage(
    wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
) -> SampleAngleStage:
    """Sample stage for p99"""

    return device_instantiation(
        SampleAngleStage,
        prefix="-MO-STAGE-01:",
        name="sample_angle_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_mock,
    )


def sample_stage_filer(
    wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
) -> FilterMotor:
    """Sample stage for p99"""

    return device_instantiation(
        FilterMotor,
        prefix="-MO-STAGE-02:MP:SELECT",
        name="sample_stage_filer",
        wait=wait_for_connection,
        fake=fake_with_ophyd_mock,
    )


def sample_xyz_stage(
    wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
) -> ThreeAxisStage:
    return device_instantiation(
        ThreeAxisStage,
        prefix="-MO-STAGE-02:",
        name="sample_xyz_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_mock,
    )


def sample_lab_xyz_stage(
    wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
) -> ThreeAxisStage:
    return device_instantiation(
        ThreeAxisStage,
        prefix="-MO-STAGE-02:LAB:",
        name="sample_lab_xyz_stage",
        wait=wait_for_connection,
        fake=fake_with_ophyd_mock,
    )


def andor2_det(
    wait_for_connection: bool = True, fake_with_ophyd_mock: bool = False
) -> Andor2Ad:
    return device_instantiation(
        Andor2Ad,
        prefix="-EA-DET-03:",
        name="andor2_det",
        path_provider=get_path_provider(),
        wait=wait_for_connection,
        fake=fake_with_ophyd_mock,
    )
