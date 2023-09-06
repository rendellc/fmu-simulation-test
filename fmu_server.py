from fmu_simulator import FMUSimulator
import traceback
import asyncio
import zmq.asyncio
import time
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


class SimulationIO:
    def __init__(self, simulator: FMUSimulator):
        print("Setting up IO")
        self.context = zmq.asyncio.Context()
        self.simulator = simulator

        inputs = self.simulator.get_input_names()
        outputs = self.simulator.get_output_names()

        print("Inputs:", inputs)
        print("Outputs:", outputs)

    async def run(self):
        await asyncio.gather(
            self.subscriber(),
            self.publisher(0.01),
        )

    async def subscriber(self):
        sub = self.context.socket(zmq.SUB)
        sub.connect("tcp://localhost:7001")
        sub.setsockopt(zmq.SUBSCRIBE, b"input")
        sub.setsockopt(zmq.SUBSCRIBE, b"reset")
        input_names = self.simulator.get_input_names()
        input_topics = list(map(lambda name: f"input/{name}".encode("utf-8"), input_names))
        for topic in input_topics:
            sub.setsockopt(zmq.SUBSCRIBE, topic)

        await asyncio.sleep(1)

        print("Subscriber topics", input_topics)
        try:
            while True:
                topic, msg = await sub.recv_multipart()
                # print(topic, msg)
                if topic == b"reset":
                    self.simulator.reset()
                elif topic == b"input":
                    pass
                else:
                    i = input_topics.index(topic)
                    input_name = input_names[i]
                    input_value = float(msg)
                    # print(f"Setting {input_name} to {input_value}")
                    self.simulator.set_input({input_name: input_value})

                # print("Received msg", msg)
        except Exception as e:
            print("Error with subscriber", e)
            print(traceback.format_exc())

    async def publisher(self, publish_period: float):
        pub = self.context.socket(zmq.PUB)
        pub.bind("tcp://*:7000")
        combined_topic = b"output"

        output_names = self.simulator.get_output_names()
        output_name_topics = list(map(lambda name: f"output/{name}".encode("utf-8"), output_names))
        print("Publisher topics", output_name_topics)

        try:
            while True:
                await asyncio.sleep(publish_period)
                output_values = self.simulator.get_output(output_names)
                data = {
                    "t": self.simulator.t,
                }
                for output_name, output_value in zip(output_names, output_values):
                    data[output_name] = output_value

                data_serialized = json.dumps(data).encode("utf-8")
                await pub.send_multipart([combined_topic, data_serialized])
                for topic, value in zip(output_name_topics, output_values):
                    await pub.send_multipart([topic, json.dumps(value).encode("utf-8")])

        except Exception as e:
            print("Error with publisher", e)
            print(traceback.format_exc())


async def simulation_loop(
    simulator: FMUSimulator, dt: float = 0.01, stop_time: float = 1000.0
):
    print("Starting simulation loop")
    while simulator.t < stop_time:
        simulator.step(dt)

        await asyncio.sleep(dt)


async def simulator_plotter(simulator: FMUSimulator, update_period: float):

    output_names = simulator.get_output_names()
    figs = []

    for output_name in output_names:
        fig, ax = plt.subplots(1, 1)
        line, = ax.plot([], [])
        ax.set_title(output_name)
        ax.set_xlabel("Time [s]")
        ax.set_xlim(0, 10)

        fig.canvas.draw()
        plt.pause(0.000001)
        background = fig.canvas.copy_from_bbox(ax.bbox)
        figs.append((fig, ax, line, background))

    plt.show(block=False)
    while True:
        t = simulator.t
        output_values = simulator.get_output(output_names)
        
        for i in range(len(output_names)):
            fig, ax, line, background = figs[i]
            x = [*line.get_xdata(), t]
            y = [*line.get_ydata(), output_values[i]]
            line.set_data(x, y)
            ax.set_xlim(0, x[~0])
            ylim = ax.get_ylim()
            ax.set_ylim(min(ylim[0], y[~0]), max(ylim[1], y[~0]))

            fig.canvas.restore_region(background)
            ax.draw_artist(line)
            fig.canvas.blit(ax.bbox)
            fig.canvas.flush_events()

        await asyncio.sleep(update_period)


async def main(enable_plotting=True):
    dt = 0.1
    simulator = FMUSimulator(
        "models/MassSpringDamper.fmu", 0.0, {"m": 1.0, "d": 0.01, "k": 1.0}
    )
    # simulator = FMUSimulator(
    #     Path("C:/Users/s29259/AppData/Local/Temp/OpenModelica/OMEdit/Ums/Ums.fmu"),
    #     0.0,
    #     {},
    # )
    io_handler = SimulationIO(simulator)
    coroutines = [simulation_loop(simulator, dt=dt), io_handler.run()]

    if enable_plotting:
        coroutines.append(simulator_plotter(simulator, 0.1))

    await asyncio.gather(*coroutines)


if __name__ == "__main__":
    from sys import argv

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main("--plot" in argv))

