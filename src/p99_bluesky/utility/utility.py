from math import ceil


def step_size_to_step_num(start: float, end: float, step_size: float):
    """Quick conversion to step from step size

    Parameters
    ----------
    start : float
        starting position
    end: float
        ending position
    step_size: float
        step size

    Returns
    -------
        Number of steps : int

    """
    step_range = abs(start - end)
    return ceil(step_range / step_size)
