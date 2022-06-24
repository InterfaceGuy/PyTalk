import c4d


def average_color(color1, color2):
    # gives the correct average of two colors
    x1 = color1.x
    y1 = color1.y
    z1 = color1.z

    x2 = color2.x
    y2 = color2.y
    z2 = color2.z

    average_x = (x1**2 + x2**2) / 2**0.5
    average_y = (y1**2 + y2**2) / 2**0.5
    average_z = (z1**2 + z2**2) / 2**0.5

    average_color = c4d.Vector(average_x, average_y, average_z)
    return average_color


def match_indices(indices1, indices2):
    # matches indices in the most natural way
    if indices1 >= indices2:
        m = indices1
        n = indices2
    else:
        m = indices2
        n = indices1
    divider, rest = divmod(m, n)
    indices_m = range(m)
    indices_n = []
    for j in range(n):
        indices_n += [j] * divider
        if rest > 0:
            indices_n += [j]
            rest -= 1
    if indices1 >= indices2:
        return indices_m, indices_n
    else:
        return indices_n, indices_m
