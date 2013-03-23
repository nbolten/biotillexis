

def map_to_plate(x, y, reference_pixels, reference_mm):
    '''Maps pixel xy coordinates to RepRap move coordinates, in mm. Requires
       an input of the Rep Rap coordinates (mm) of each pink dot when
       it's just below the pipet tip.'''

    ref1_pixels = reference_pixels[0]
    ref2_pixels = reference_pixels[1]
    ref3_pixels = reference_pixels[2]
    ref4_pixels = reference_pixels[4]
    ref1_mm = reference_mm[0]
    ref2_mm = reference_mm[1]
    ref3_mm = reference_mm[2]
    ref4_mm = reference_mm[3]

    # Find min / max points for x and y in both image pixels and mm
    x_max_ref_pixels = ref1_pixels[0]
    x_min_ref_pixels = ref2_pixels[0]
    x_max_ref_mm = ref1_mm[0]
    x_min_ref_mm = ref2_mm[0]
    y_max_ref_pixels = ref1_pixels[1]
    y_min_ref_pixels = ref3_pixels[1]
    y_max_ref_mm = ref1_mm[1]
    y_min_ref_mm = ref3_mm[1]

    # Find the distance between the min/max points of the reference in
    # both pixels and mm
    x_span_pixels = x_max_ref_pixels - x_min_ref_pixels
    x_span_mm = x_max_ref_mm - x_min_ref_mm
    y_span_pixels = y_max_ref_pixels - y_min_ref_pixels
    y_span_mm = y_max_ref_mm - y_min_ref_mm

    # Translate the input xy pixels coordinates into rep rap moves by
    # interpolating - calculation assumes the references have a square shape
    # and are aligned with the camera
    # TODO: are these functions redundant?
    def x_trans(x_point):
        ratio = float(x_span_mm) / x_span_pixels
        difference = x_max_ref_pixels - x_point
        adjustment = x_max_ref_mm
        return -1 * ratio * difference + adjustment

    def y_trans(y_point):
        ratio = float(y_span_mm) / y_span_pixels
        difference = y_max_ref_pixels - y_point
        adjustment = y_max_ref_mm
        return -1 * ratio * difference + adjustment

    move_x = x_trans(x)
    move_y = y_trans(y)
    return (move_x, move_y)
