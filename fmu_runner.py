import numpy as np
from fmu_simulator import FMUSimulator
import matplotlib.pyplot as plt

fmu_path = "models/MassSpringDamper.fmu"
rows = []
simulator = FMUSimulator("models/MassSpringDamper.fmu", 0.0, {"m": 10.0, "d": 1.0, "k": 2.0 })
x_target = 10.0

x_error = 0.0
x_error_integral = 0.0

def controller(t, dt, x):
    global x_error, x_error_integral
    x_error_prev = x_error
    x_error = x_target - x
    x_error_derivative = (x_error - x_error_prev)/dt
    x_error_integral += x_error*dt

    u = 10.0*x_error + 2.0*x_error_derivative + 1.0*x_error_integral

    return u


stop_time = 100.0
dt = 0.1

while simulator.t < stop_time:
    x = simulator.get_output()
    u = controller(simulator.t, dt, x)
    simulator.set_input(u)
    simulator.step(dt)

    rows.append((simulator.t, x, x_error, u))


result = np.array(rows, dtype=np.dtype([
    ('time', np.float64),
    ('x', np.float64),
    ('x_error', np.float64),
    ('u', np.float64)]))


fix, axs = plt.subplots(2,1)
axs[0].plot(result["time"], result["x"])
axs[0].plot(result["time"], result["x_error"])
axs[1].plot(result["time"], result["u"])

plt.show()
