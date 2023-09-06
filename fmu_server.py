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
        sub.connect("tcp://localhost:7000")
        sub.setsockopt(zmq.SUBSCRIBE, b"input")
        input_names = self.simulator.get_input_names()
        for input_name in input_names:
            sub.setsockopt(zmq.SUBSCRIBE, input_name.encode("utf-8"))

        await asyncio.sleep(1)

        print("Running subscriber")
        try:
            while True:
                topic, msg = await sub.recv_multipart()
                print("Received msg", msg)
        except Exception as e:
            print("Error with subscriber", e)
            print(traceback.format_exc())

    async def publisher(self, publish_period: float):
        pub = self.context.socket(zmq.PUB)
        pub.bind("tcp://*:7000")
        combined_topic = b"output"

        output_names = self.simulator.get_output_names()
        output_name_topics = list(map(lambda name: name.encode("utf-8"), output_names))
        print("Running publisher")

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
    simulator: FMUSimulator, dt: float = 0.01, stop_time: float = 10.0
):
    print("Starting simulation loop")
    while simulator.t < stop_time:
        simulator.step(dt)

        await asyncio.sleep(dt)


async def test_subscriber():
    context = zmq.asyncio.Context()
    sub = context.socket(zmq.SUB)
    sub.connect("tcp://localhost:7000")
    sub.setsockopt(zmq.SUBSCRIBE, b"output")
    sub.setsockopt(zmq.SUBSCRIBE, b"x")

    await asyncio.sleep(1)

    print("Running subscriber")
    try:
        while True:
            topic, msg = await sub.recv_multipart()
            print("Test: ", msg)
    except Exception as e:
        print("Error with test subscriber", e)
        print(traceback.format_exc())


async def simulator_plotter(simulator: FMUSimulator, update_period: float):
    fig, axs = plt.sublots(2, 1)

    while True:
        await asyncio.sleep(update_period)


async def main():
    dt = 0.1
    simulator = FMUSimulator(
        "models/MassSpringDamper.fmu", 0.0, {"m": 10.0, "d": 1.0, "k": 2.0}
    )
    # simulator = FMUSimulator(
    #     Path("C:/Users/s29259/AppData/Local/Temp/OpenModelica/OMEdit/Ums/Ums.fmu"),
    #     0.0,
    #     {},
    # )
    io_handler = SimulationIO(simulator)

    await asyncio.gather(simulation_loop(simulator, dt=dt), io_handler.run())


if __name__ == "__main__":
    from sys import argv

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    if len(argv) >= 2 and argv[1] == "test_client":
        asyncio.run(test_subscriber())
        sys.exit(0)

    asyncio.run(main())
