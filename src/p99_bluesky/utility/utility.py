from math import ceil

from scanspec.specs import Line


def get_lines_from_range(
    x_step_start,
    x_step_end,
    x_step_size,
    y_step_start,
    y_step_end,
    y_step_size,
    snake=False,
) -> Line:
    if snake:
        spec = Line(
            "x",
            x_step_start,
            x_step_end,
            step_size_to_step_num(x_step_start, x_step_end, x_step_size),
        ) * ~Line(
            "y",
            y_step_start,
            y_step_end,
            step_size_to_step_num(y_step_start, y_step_end, y_step_size),
        )
    else:
        spec = Line(
            "x",
            x_step_start,
            x_step_end,
            step_size_to_step_num(x_step_start, x_step_end, x_step_size),
        ) * Line(
            "y",
            y_step_start,
            y_step_end,
            step_size_to_step_num(y_step_start, y_step_end, y_step_size),
        )
    return spec


def step_size_to_step_num(start, end, step_size):
    step_range = abs(start - end)
    return ceil(step_range / step_size)
