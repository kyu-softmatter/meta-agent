"""The measurement error of a measured value against a reference value, and its magnitude."""


def analysis(inputs):
    error = inputs["measured"] - inputs["reference"]
    return {"error": error, "magnitude": abs(error)}
