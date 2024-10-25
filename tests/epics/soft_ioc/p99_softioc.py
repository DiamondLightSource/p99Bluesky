import asyncio

from softioc import asyncio_dispatcher, builder, softioc
from softsignal import soft_mbb, soft_motor, soft_signal


async def p99_fake() -> None:
    async def _delay_move(signal, v, vel, dmov):
        diff = signal.get() - v.get()
        if abs(diff) < vel.get() * 0.04:
            signal.set(v.get())
            dmov.set(True)

        elif diff < 0:
            dmov.set(False)
            signal.set(signal.get() + vel.get() * 0.01)
        elif diff > 0:
            dmov.set(False)
            signal.set(signal.get() - vel.get() * 0.01)

    # Sample AngleStage softioc
    dispatcher = asyncio_dispatcher.AsyncioDispatcher()
    soft_signal("p99-MO-TABLE-01", "WRITETHETA", "WRITETHETA:RBV")
    soft_signal("p99-MO-TABLE-01", "WRITEROLL", "WRITEROLL:RBV")
    soft_signal("p99-MO-TABLE-01", "WRITEPITCH", "WRITEPITCH:RBV")
    # sample selection staged
    soft_mbb("p99-MO-STAGE-02", "MP:SELECT")
    # xyz stage
    x_set, x_vel, x_rbv, x_dmov = await soft_motor(
        prefix="p99-MO-STAGE-02", name="X", unit="mm"
    )
    y_set, y_vel, y_rbv, y_dmov = await soft_motor(
        prefix="p99-MO-STAGE-02", name="Y", unit="mm"
    )
    z_set, z_vel, z_rbv, z_dmov = await soft_motor(
        prefix="p99-MO-STAGE-02", name="Z", unit="mm"
    )
    # build the ioc
    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    # print(softioc.dbnr(), softioc.dbl())  # type: ignore

    async def update(y_rbv, y_set, y_vel, y_dmov):
        await _delay_move(y_rbv, y_set, y_vel, y_dmov)

    while True:
        dispatcher(update, [z_rbv, z_set, z_vel, z_dmov])
        dispatcher(update, [y_rbv, y_set, y_vel, y_dmov])
        dispatcher(update, [x_rbv, x_set, x_vel, x_dmov])
        await asyncio.sleep(0.01)
    # softioc.interactive_ioc(globals())


if __name__ == "__main__":
    asyncio.run(p99_fake())
