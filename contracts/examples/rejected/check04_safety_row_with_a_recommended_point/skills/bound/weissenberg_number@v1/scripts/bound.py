"""The Weissenberg number of a shear flow."""


def bound(inputs):
    return {"weissenberg_number": inputs["relaxation_time"] * inputs["shear_rate"]}
