def map_to_plate(x, y, reference_points=None):
    # If given an input of four reference points (tuple or list),
    # use them to generate the move. Otherwise, use a manually-determined
    # set of baseline coordinates
    if not reference_points:
        ref1_pixels = (351, 118)
        ref2_pixels = (894, 118)
        ref3_pixels = (920, 608)
        ref4_pixels = (334, 608)
    else:
        ref1_pixels = reference_points(0)
        ref2_pixels = reference_points(1)
        ref3_pixels = reference_points(2)
        ref4_pixels = reference_points(4)

    # Manually calibrated absolute coordinates for rep rap to move to
    # each point
    ref1_mm = (61, 87)
    ref2_mm = (18, 87)
    ref3_mm = (18, 125)
    ref4_mm = (61, 125)

    # Find min / max points for x and y in both image pixels and mm
    x_max_ref_pixels = ref1_pixels[0]
    x_min_ref_pixels = ref2_pixels[0]
    x_max_ref_mm = ref1_mm[0]
    x_min_ref_mm = ref2_mm[0]
    y_max_ref_pixels = ref1_pixels[1]
    y_min_ref_pixels = ref3_pixels[1]
    y_max_ref_mm = ref1_mm[1]
    y_min_ref_mm = ref3_mm[1]

    # Find the distance between the min/max points fo the reference in
    # both pixels and mm
    x_span_pixels = x_max_ref_pixels - x_min_ref_pixels
    x_span_mm = x_max_ref_mm - x_min_ref_mm
    y_span_pixels = y_max_ref_pixels - y_min_ref_pixels
    y_span_mm = y_max_ref_mm - y_min_ref_mm

    # Translate the input xy pixels coordinates into rep rap moves by
    # interpolating - calculation assumes the references had a square shape
    # that's aligned with the camera
    def x_trans(x_point):
        return -1* float(x_span_mm) / x_span_pixels * (x_max_ref_pixels - x_point) + x_max_ref_mm

    def y_trans(y_point):
        return -1 * float(y_span_mm) / y_span_pixels * (y_max_ref_pixels - y_point) + y_max_ref_mm

    move_x = x_trans(x)
    move_y = y_trans(y)
    return (move_x, move_y)
