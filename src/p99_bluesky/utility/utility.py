from math import ceil


# quick conversion to step from step size
def step_size_to_step_num(start, end, step_size):
    step_range = abs(start - end)
    return ceil(step_range / step_size)
