from fmu_simulator import FMUSimulator
import traceback
import asyncio
import zmq.asyncio
import time
import json


class SimulationIO:
    def __init__(self, simulator: FMUSimulator):
        print("Setting up IO")
        self.context = zmq.asyncio.Context()
        self.simulator = simulator
        

    async def run(self):
        await asyncio.gather(
            self.subscriber(),
            self.publisher(),
        )


    async def subscriber(self):
        sub = self.context.socket(zmq.SUB)
        sub.connect("tcp://localhost:7000")
        sub.setsockopt(zmq.SUBSCRIBE, b"input")

        await asyncio.sleep(1)

        print("Running subscriber")
        try:
            while True:
                msg = await sub.recv_multipart()
                print("Received msg", msg)
        except Exception as e:
            print("Error with subscriber", e)
            print(traceback.format_exc())



    async def publisher(self):
        pub = self.context.socket(zmq.PUB)
        pub.bind("tcp://*:7001")
        topic = b"output"

        print("Running publisher")
        try:
            while True:
                await asyncio.sleep(1)
                x = self.simulator.get_output()
                data = {
                    "t": self.simulator.t,
                    "x": x,
                }
                data_serialized = json.dumps(data).encode("utf-8")
                await pub.send_multipart([topic, data_serialized])
                print(f"Published: {data_serialized}")
        except Exception as e:
            print("Error with publisher", e)
            print(traceback.format_exc())


async def simulation_loop(simulator: FMUSimulator, dt: float = 0.1, stop_time: float = 10.0):
    print("Starting simulation loop")
    while simulator.t < stop_time:
        simulator.step(dt)
        print(f"Simulation time: {simulator.t}")

        await asyncio.sleep(dt)

async def main():
    simulator = FMUSimulator("models/MassSpringDamper.fmu", 0.0, {"m": 10.0, "d": 1.0, "k": 2.0 })
    io_handler = SimulationIO(simulator)

    await asyncio.gather(simulation_loop(simulator), io_handler.run())


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

