import asyncio
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DeviceCollector
from super_state_machine.errors import TransitionError

from soft_motor import SoftThreeAxisStage

RECORD = str(Path(__file__).parent / "panda" / "db" / "panda.db")
INCOMPLETE_BLOCK_RECORD = str(
    Path(__file__).parent / "panda" / "db" / "incomplete_block_panda.db"
)
INCOMPLETE_RECORD = str(Path(__file__).parent / "panda" / "db" / "incomplete_panda.db")
EXTRA_BLOCKS_RECORD = str(
    Path(__file__).parent / "panda" / "db" / "extra_blocks_panda.db"
)


@pytest.fixture(scope="session")
def RE(request):
    loop = asyncio.new_event_loop()
    loop.set_debug(True)
    RE = RunEngine({}, call_returns_result=True, loop=loop)

    def clean_event_loop():
        if RE.state not in ("idle", "panicked"):
            try:
                RE.halt()
            except TransitionError:
                pass
        loop.call_soon_threadsafe(loop.stop)
        RE._th.join()
        loop.close()

    request.addfinalizer(clean_event_loop)
    return RE


@pytest.fixture(scope="module", params=["pva"])
def pva():
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "epicscorelibs.ioc",
                "-m",
                macros,
                "-d",
                RECORD,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        for macros in [
            "INCLUDE_EXTRA_BLOCK=,INCLUDE_EXTRA_SIGNAL=",
            "EXCLUDE_WIDTH=#,IOC_NAME=PANDAQSRVIB",
            "EXCLUDE_PCAP=#,IOC_NAME=PANDAQSRVI",
        ]
    ]
    time.sleep(2)

    for p in processes:
        assert not p.poll()  # , p.stdout.read()

    yield processes

    for p in processes:
        p.terminate()
        p.communicate()


@pytest.fixture
async def normal_coroutine() -> Callable[[], Any]:
    async def inner_coroutine():
        await asyncio.sleep(0.01)

    return inner_coroutine


@pytest.fixture
async def failing_coroutine() -> Callable[[], Any]:
    async def inner_coroutine():
        await asyncio.sleep(0.01)
        raise ValueError()

    return inner_coroutine


A_BIT = 0.5


@pytest.fixture(scope="session")
async def fake_99():
    p = subprocess.Popen(
        [
            "python",
            "tests/epics/soft_ioc/p99_softioc.py",
        ],
    )

    # Give the server time to start
    await asyncio.sleep(A_BIT)
    # Check it started successfully
    print("setup")
    yield p
    p.terminate()
    # Shut it down at the
    p.wait()
    await asyncio.sleep(A_BIT)


@pytest.fixture(scope="session")
def xyz_motor(fake_99):
    with DeviceCollector(mock=False):
        xyz_motor = SoftThreeAxisStage("p99-MO-STAGE-02:", name="xyz_motor")
    yield xyz_motor
