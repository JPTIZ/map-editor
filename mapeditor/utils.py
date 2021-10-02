from PySide2.QtCore import QRect

def print_table(srcs, dsts):
    print("table:\n[ ")
    for src_line, dst_line in zip(srcs, dsts):
        print("  [", end="")
        for x, y in src_line:
            print(f"{x:>2},{y:>2}:", end="")
        if srcs:
            print("  ->  ", end="")
            for x, y in dst_line:
                print(f"{x:>2},{y:>2}:", end="")
        print(" ]")
    print("]")


def print_dict(srcs, dsts, name='dict'):
    print(f"{name}: {{")
    max_len = max(len(xs) for xs in [*srcs.values(), *dsts.values()])
    for sy, dy in zip(srcs, dsts):
        print(f"  {sy:>2}: [", end="")
        for x in srcs.get(sy, [''] * max_len):
            print(f"{x:>2}:", end="")
        print(f"]  ->  {dy:>2}: [", end="")
        for x in dsts.get(dy, [''] * max_len):
            print(f"{x:>2}:", end="")
        print(" ]")
    print("}")


def bound_to_range(value: int, limits: tuple[int, int]):
    _min, _max = limits
    return max(_min, min(_max, value))

def bound_to_rect(rect: QRect, bounds: QRect):
    return QRect(
        bound_to_range(rect.x(), (0, bounds.width())),
        bound_to_range(rect.y(), (0, bounds.height())),
        bound_to_range(rect.width(), (0, bounds.width())),
        bound_to_range(rect.height(), (0, bounds.height())),
    )


def scaled(rect: QRect, scale: int):
    rect = QRect(
        rect.x() * scale, rect.y() * scale, rect.width() * scale, rect.height() * scale
    )
    return rect
