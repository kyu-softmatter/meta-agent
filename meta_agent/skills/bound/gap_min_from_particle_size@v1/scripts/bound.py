"""Lower bound on the measuring gap: a stated multiple of the largest particle diameter."""


def bound(inputs):
    return {"gap_min": inputs["gap_to_particle_ratio"] * inputs["particle_diameter"]}
