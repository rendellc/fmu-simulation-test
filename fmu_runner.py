import numpy as np
from pathlib import Path
from fmu_simulator import FMUSimulator
import matplotlib.pyplot as plt


class Controller:
    def __init__(self, simulator: FMUSimulator):
        self.simulator = simulator

    def update(self):
        # Read out state data from simulator
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


fmu_path = Path("C:/Users/s29259/AppData/Local/Temp/OpenModelica/OMEdit/Ums/Ums.fmu")
rows = []
simulator = FMUSimulator(fmu_path, 0.0, {})
controller = Controller(simulator)

stop_time = 100.0
dt = 0.1

while simulator.t < stop_time:
    drum_motor_torque, sheave_motor_torque = controller.update()

    simulator.set_input(
        {
            "drum_motor_torque": drum_motor_torque,
            "sheave_motor_torque": sheave_motor_torque,
        }
    )
    simulator.step(dt)


# result = np.array(
#     rows,
#     dtype=np.dtype(
#         [
#             ("time", np.float64),
#             ("drum_speed_setpoint", np.float64),
#             ("drum_speed", np.float64),
#             ("drum_motor_torque", np.float64),
#         ]
#     ),
# )


fix, axs = plt.subplots(2, 1)
axs[0].plot(result["time"], result["drum_speed"])
axs[0].plot(result["time"], result["drum_speed_setpoint"])
axs[1].plot(result["time"], result["drum_motor_torque"])

plt.show()
