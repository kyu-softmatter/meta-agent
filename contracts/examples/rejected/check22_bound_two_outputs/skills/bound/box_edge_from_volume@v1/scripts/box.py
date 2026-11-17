"""The edge of a cube from its volume."""


def box_edge(inputs):
    edge = inputs["box_volume"] ** (1.0 / 3.0)
    return {"box_edge": edge, "face_area": edge * edge}
