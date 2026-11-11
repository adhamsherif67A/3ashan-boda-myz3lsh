"""Bottom-camera transect detector used by the fly-transect mission.

Pure image processing: no ROS node, no topics. Give it a sensor_msgs/Image
(rgb8, bgr8, rgba8 or bgra8) and it returns what it sees in the pool transect:
the two blue rails, red boundary rails inside the corridor, and the black end bar.
"""
import math


def _components(mask, width, height):
    """Return connected components as sampled (x, y) grid coordinates."""
    seen = bytearray(len(mask))
    components = []
    for start, active in enumerate(mask):
        if not active or seen[start]:
            continue
        seen[start] = 1
        pending = [start]
        points = []
        while pending:
            index = pending.pop()
            x, y = index % width, index // width
            points.append((x, y))
            if x and mask[index - 1] and not seen[index - 1]:
                seen[index - 1] = 1
                pending.append(index - 1)
            if x + 1 < width and mask[index + 1] and not seen[index + 1]:
                seen[index + 1] = 1
                pending.append(index + 1)
            if y and mask[index - width] and not seen[index - width]:
                seen[index - width] = 1
                pending.append(index - width)
            if y + 1 < height and mask[index + width] and not seen[index + width]:
                seen[index + width] = 1
                pending.append(index + width)
        components.append(points)
    return components


def _line_axis(points):
    """Return centroid, major-axis angle, elongation, and major extent."""
    count = len(points)
    if count < 2:
        return None
    mean_x = sum(point[0] for point in points) / count
    mean_y = sum(point[1] for point in points) / count
    xx = sum((point[0] - mean_x) ** 2 for point in points) / count
    yy = sum((point[1] - mean_y) ** 2 for point in points) / count
    xy = sum((point[0] - mean_x) * (point[1] - mean_y) for point in points) / count
    root = math.sqrt(max(0.0, (xx - yy) ** 2 + 4 * xy * xy))
    major = max(0.0, (xx + yy + root) * 0.5)
    minor = max(0.0, (xx + yy - root) * 0.5)
    angle = 0.5 * math.atan2(2 * xy, xx - yy)
    extent = max(
        abs((point[0] - mean_x) * math.cos(angle) +
            (point[1] - mean_y) * math.sin(angle))
        for point in points
    ) * 2.0
    elongation = math.sqrt(major / max(minor, 0.25))
    return mean_x, mean_y, angle, elongation, extent


def detect_transect(message, stride=6):
    """Detect the two blue rails, red boundary rails, and black end bars."""
    encoding = message.encoding.lower()
    if encoding not in ('rgb8', 'bgr8', 'rgba8', 'bgra8'):
        raise ValueError(f'unsupported bottom-camera encoding: {message.encoding}')
    channels = 4 if 'a8' in encoding else 3
    width, height = int(message.width), int(message.height)
    if width <= 0 or height <= 0 or message.step < width * channels:
        raise ValueError('invalid bottom-camera image dimensions or row stride')
    data = message.data
    if len(data) < message.step * height:
        raise ValueError('incomplete bottom-camera image')
    grid_width = (width + stride - 1) // stride
    grid_height = (height + stride - 1) // stride
    blue = bytearray(grid_width * grid_height)
    red = bytearray(grid_width * grid_height)
    black = bytearray(grid_width * grid_height)
    blue_count = red_count = 0
    rgb_order = encoding.startswith('rgb')
    for gy in range(grid_height):
        row = gy * stride * message.step
        for gx in range(grid_width):
            offset = row + gx * stride * channels
            first, green, third = data[offset], data[offset + 1], data[offset + 2]
            r, b = (first, third) if rgb_order else (third, first)
            index = gy * grid_width + gx
            # Require saturated blue rather than merely a larger blue
            # channel. The pool tiles are cyan/grey and otherwise create
            # long false components that resemble the transect rails.
            if (b > 55 and b > r + 35 and b > green + 25 and
                    b > r * 1.35):
                blue[index] = 1
                blue_count += 1
            if r > 35 and r > green * 1.15 and r > b * 1.15:
                red[index] = 1
                red_count += 1
            if max(r, green, b) < 62:
                black[index] = 1

    blue_lines = []
    for points in _components(blue, grid_width, grid_height):
        stats = _line_axis(points)
        if stats and len(points) >= 5 and stats[3] >= 2.0 and stats[4] >= 6:
            blue_lines.append((len(points), stats))
    blue_lines.sort(key=lambda item: item[0], reverse=True)
    blue_pair = False
    blue_midpoint = None
    if len(blue_lines) >= 2:
        first, second = blue_lines[:2]
        angle_delta = abs((first[1][2] - second[1][2] + math.pi / 2) % math.pi - math.pi / 2)
        delta_x = abs(first[1][0] - second[1][0])
        delta_y = abs(first[1][1] - second[1][1])
        separation = math.hypot(delta_x, delta_y)
        vertical_first = abs((first[1][2] - math.pi / 2 + math.pi / 2) % math.pi - math.pi / 2)
        vertical_second = abs((second[1][2] - math.pi / 2 + math.pi / 2) % math.pi - math.pi / 2)
        # In the bottom view, the longitudinal rails run nearly vertically
        # and are separated across the image. Tile seams can be blue too, but
        # they are short, horizontal, or do not form this pair.
        blue_pair = (
            angle_delta < 0.35 and
            vertical_first < 0.45 and
            vertical_second < 0.45 and
            delta_x >= 8 and
            delta_y <= delta_x * 0.65 and
            separation >= 8
        )
        if blue_pair:
            blue_midpoint = ((first[1][0] + second[1][0]) * 0.5 * stride,
                             (first[1][1] + second[1][1]) * 0.5 * stride)

    red_lines = []
    for points in _components(red, grid_width, grid_height):
        stats = _line_axis(points)
        if stats and len(points) >= 5 and stats[3] >= 2.0 and stats[4] >= 6:
            red_lines.append(stats)
    red_seen = bool(red_lines)
    if blue_pair and red_lines:
        # The outer red rails are expected in the wide bottom-camera view.
        # Only treat a red line as a blocker when it intrudes into the
        # corridor bounded by the two blue rails.
        rail_angle = blue_lines[0][1][2]
        normal_x, normal_y = -math.sin(rail_angle), math.cos(rail_angle)
        blue_projection = [
            line[0] * normal_x + line[1] * normal_y
            for _, line in blue_lines[:2]
        ]
        lower = min(blue_projection) - 0.15 * abs(blue_projection[0] - blue_projection[1])
        upper = max(blue_projection) + 0.15 * abs(blue_projection[0] - blue_projection[1])
        red_seen = any(lower <= stats[0] * normal_x + stats[1] * normal_y <= upper
                       for stats in red_lines)
    black_bar = False
    for points in _components(black, grid_width, grid_height):
        stats = _line_axis(points)
        if not stats or len(points) < 8 or stats[3] < 3.0 or stats[4] < 10:
            continue
        # The transect's black marker crosses the blue rails, so the axes
        # should be close to perpendicular in the bottom-camera image.
        if blue_pair:
            rail_angle = blue_lines[0][1][2]
            cross_angle = abs((stats[2] - rail_angle + math.pi / 2) % math.pi - math.pi / 2)
            if abs(cross_angle - math.pi / 2) > 0.55:
                continue
        black_bar = True
        break
    return {
        'blue_pair': blue_pair,
        'blue_count': len(blue_lines),
        'blue_midpoint': blue_midpoint,
        'red_seen': red_seen,
        'red_count': red_count,
        'black_bar': black_bar,
    }
