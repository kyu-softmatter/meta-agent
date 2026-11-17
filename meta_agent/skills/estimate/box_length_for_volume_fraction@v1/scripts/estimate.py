"""The side of a cubic box for a number of particles of a given volume at a given volume fraction."""


def estimate(inputs):
    phi = inputs["volume_fraction"]
    if not 0 < phi < 1:
        raise ValueError("volume_fraction must lie above zero and below one")
    volume = inputs["particle_count"] * inputs["particle_volume"] / phi
    return {"box_length": volume ** (1.0 / 3.0), "box_volume": volume}
