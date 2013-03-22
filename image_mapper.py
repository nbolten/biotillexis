def map_to_plate(x, y):
    dot1_pixels = (351, 118)
    dot2_pixels = (894, 118)
    dot3_pixels = (920, 608)
    dot4_pixels = (334, 608)
    dot1_mm = (61, 87)
    dot2_mm = (18, 87)
    dot3_mm = (18, 125)
    dot4_mm = (61, 125)

    x_max_ref_pixels = dot1_pixels[0]
    x_min_ref_pixels = dot2_pixels[0]
    x_max_ref_mm = dot1_mm[0]
    x_min_ref_mm = dot2_mm[0]
    y_max_ref_pixels = dot1_pixels[1]
    y_min_ref_pixels = dot3_pixels[1]
    y_max_ref_mm = dot1_mm[1]
    y_min_ref_mm = dot3_mm[1]

    x_span_pixels = x_max_ref_pixels - x_min_ref_pixels
    x_span_mm = x_max_ref_mm - x_min_ref_mm
    y_span_pixels = y_max_ref_pixels - y_min_ref_pixels
    y_span_mm = y_max_ref_mm - y_min_ref_mm

    def x_trans(x_point):
        return -1* float(x_span_mm) / x_span_pixels * (x_max_ref_pixels - x_point) + x_max_ref_mm

    def y_trans(y_point):
        return -1 * float(y_span_mm) / y_span_pixels * (y_max_ref_pixels - y_point) + y_max_ref_mm

    move_x = x_trans(x)
    move_y = y_trans(y)
    return (move_x, move_y)
