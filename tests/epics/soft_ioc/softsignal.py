from softioc import builder


def soft_signal(prefix: str, input_name: str, readback_name: str) -> None:
    # Create some records
    builder.SetDeviceName(prefix)
    rbv = builder.aIn(readback_name, initial_value=0)
    # rbv.append(temp)
    builder.aOut(
        input_name,
        initial_value=0.1,
        always_update=True,
        on_update=lambda v: rbv.set(v),
    )


def soft_mbb(prefix: str, name: str, *option):
    builder.SetDeviceName(prefix)
    # temp = builder.mbbIn(readback_name, initial_value=0)
    builder.mbbOut(
        name,
        "Empty",
        "Mn 5um",
        "Fe (empty)",
        "Co 5um",
        "Ni 5um",
        "Cu 5um",
        "Zn 5um",
        "Zr (empty)",
        "Mo (empty)",
        "Rh (empty)",
        "Pd (empty)",
        "Ag (empty)",
        "Cd 25um",
        "W (empty)",
        "Pt (empty)",
        "User",
    )


async def soft_motor(prefix: str, name: str, unit: str = "mm"):
    builder.SetDeviceName(prefix)
    builder.aOut(
        name,
        initial_value=1.1,
        EGU=unit,
        VAL=1.1,
        PREC=0,
    )
    rbv = builder.aOut(
        name + "RBV",
        initial_value=0.0,
    )
    vel = builder.aOut(
        name + "VELO",
        initial_value=1000,
    )
    dmov = builder.boolOut(
        name + "DMOV",
        initial_value=True,
    )
    ai = builder.aOut(
        name + "VAL",
        initial_value=0.0,
        always_update=True,
        on_update=lambda v: dmov.set(False),
    )

    builder.aOut(
        name + "VMAX",
        initial_value=200,
    )
    builder.aOut(
        name + "ACCL",
        initial_value=0.01,
    )
    builder.aOut(
        name + "RDBD",
        initial_value=0.1,
    )

    builder.aOut(
        name + "LLM",
        initial_value=-100,
    )
    builder.aOut(
        name + "HLM",
        initial_value=100,
    )
    builder.aOut(
        name + "STOP",
        initial_value=0,
    )
    return ai, vel, rbv, dmov
