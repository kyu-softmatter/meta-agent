"""A fixture script: the rich lab runs Brownian dynamics in HOOMD-blue on a GPU."""
import hoomd

device = hoomd.device.GPU()
sim = hoomd.Simulation(device=device, seed=1)
