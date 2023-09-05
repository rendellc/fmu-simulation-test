import zmq
import zmq.asyncio
import pathlib
from fmu_simulator import FMUSimulator
import asyncio


async def run_publisher(simout_queue):
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:5555")
    state_topic = "state".encode("utf-8")

    while True:
        data = await simout_queue.get()
        if data is None:
            break

        print("Publisher:", data)

        simout_queue.task_done()



async def run_simulator(simulator, simin_queue, simout_queue):
    # TODO: Add controller for dt to sync with time
    dt = 0.2
    u = 0.0
    while simulator.t < 10:
        if not simin_queue.empty():
            u = await simin_queue.get()

        simulator.set_input(u)
        simulator.step(dt)
        x = simulator.get_output()
        await simout_queue.put((simulator.t, x, u))
        await asyncio.sleep(dt)

    simout_queue.put(None)

async def run_controller(simin_queue):
    await simin_queue.put(0)
    await asyncio.sleep(1)
    await simin_queue.put(1)
    await asyncio.sleep(1)
    await simin_queue.put(2)
    await asyncio.sleep(1)
    await simin_queue.put(-3)
    await asyncio.sleep(1)

async def main():
    start_time = 0.0
    simulator = FMUSimulator("models/MassSpringDamper.fmu", 0.0, {"m": 10.0, "d": 1.0, "k": 2.0 })
    simout_queue = asyncio.Queue()
    simin_queue = asyncio.Queue()

    # asyncio.run(run_simulator(simulator))
    simulator_routine = run_simulator(simulator, simin_queue, simout_queue)
    publisher_routine = run_publisher(simout_queue)
    controller_routine = run_controller(simin_queue)

    await asyncio.gather(simulator_routine, publisher_routine, controller_routine)





if __name__=="__main__":
    asyncio.run(main())
