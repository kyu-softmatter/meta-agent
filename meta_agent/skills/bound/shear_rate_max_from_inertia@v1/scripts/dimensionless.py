"""Dimensionless numbers of a cone-and-plate flow. Plain functions: they bound nothing by themselves."""


def reynolds_cone_plate(density, shear_rate, cone_angle, cone_radius, viscosity):
    """density * angular velocity * (cone angle * radius)^2 / viscosity, with angular velocity = shear rate * cone angle."""
    return density * shear_rate * cone_angle ** 3 * cone_radius ** 2 / viscosity
