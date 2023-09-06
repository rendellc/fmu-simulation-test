import numpy as np
from pathlib import Path
from fmu_simulator import FMUSimulator
import matplotlib.pyplot as plt


class Controller:
    def __init__(self, simulator: FMUSimulator):
        self.simulator = simulator

    def update(self):
        # Read out state data from simulator
        t = simulator.t
        (
            umbilical_tension,
            filtered_umbilical_tension,
            tension_measurement,
            drum_linear_speed,
            sheave_linear_speed,
            drum_speed_setpoint,
        ) = simulator.get_output(
            [
                "umbilical_tension",
                "filtered_umbilical_tension",
                "tension_measurement",
                "drum_linear_speed_out",
                "sheave_linear_speed_out",
                "drum_speed_setpoint_out",
            ]
        )

        drum_motor_torque = 0.0
        sheave_motor_torque = 0.0

        return drum_motor_torque, sheave_motor_torque


class ControllerMassSpringDamper:
    def __init__(self, simulator: FMUSimulator):
        self.simulator = simulator
        self.x_prev = None
        self.t_prev = None
        self.x_error_integral = 0.0

    def update(self):
        # Read out state data from simulator
        x_target = 10.0
        t = simulator.t
        x, = simulator.get_output(["x"])

        x_error = x_target - x

        dt = t - self.t_prev if self.t_prev != None else None
        self.t_prev = t
        x_dot = (x - self.x_prev)/dt if (self.x_prev != None and dt != None) else 0.0
        self.x_prev = x

        self.x_error_integral += x_error * dt if dt != None else 0.0

        u = 1.0*x_error + 0.1*x_dot + 0.5 * self.x_error_integral
        return u


# fmu_path = Path("C:/Users/s29259/AppData/Local/Temp/OpenModelica/OMEdit/Ums/Ums.fmu")
fmu_path = Path("models/MassSpringDamper.fmu")
rows = []
simulator = FMUSimulator(fmu_path, 0.0, {"m": 1.0, "d": 1.0, "k": 1.0})
controller = ControllerMassSpringDamper(simulator)

stop_time = 100.0
dt = 0.01

while simulator.t < stop_time:
    # drum_motor_torque, sheave_motor_torque = controller.update()
    u = controller.update()

    simulator.set_input({"u": u})
    # simulator.set_input(
    #     {
    #         "drum_motor_torque": drum_motor_torque,
    #         "sheave_motor_torque": sheave_motor_torque,
    #     }
    # )
    simulator.step(dt)

    rows.append((simulator.t, *simulator.get_output(simulator.get_output_names()), u))

result = np.array(rows, dtype=np.dtype(
    [
        ("time", np.float64),
        *[(name, np.float64) for name in simulator.get_output_names()],
        ("u", np.float64),
    ])
)


fix, axs = plt.subplots(2, 1)
axs[0].plot(result["time"], result["x"])
axs[1].plot(result["time"], result["u"])

# axs[0].plot(result["time"], result["drum_speed"])
# axs[0].plot(result["time"], result["drum_speed_setpoint"])
# axs[1].plot(result["time"], result["drum_motor_torque"])

plt.show()
