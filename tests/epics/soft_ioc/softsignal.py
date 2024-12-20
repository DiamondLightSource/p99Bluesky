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
        "EMPTY",
        "MN 5UM",
        "FE (EMPTY)",
        "CO 5UM",
        "NI 5UM",
        "CU 5UM",
        "ZN 5UM",
        "ZR (EMPTY)",
        "MO (EMPTY)",
        "RH (EMPTY)",
        "PD (EMPTY)",
        "AG (EMPTY)",
        "CD 25UM",
        "W (EMPTY)",
        "PT (EMPTY)",
        "USER",
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
