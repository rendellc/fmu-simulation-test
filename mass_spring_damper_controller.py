import asyncio
import traceback
import json
import zmq
import zmq.asyncio


async def controller():
    context = zmq.asyncio.Context()
    sub = context.socket(zmq.SUB)
    sub.connect("tcp://localhost:7000")
    sub.setsockopt(zmq.SUBSCRIBE, b"output")

    pub = context.socket(zmq.PUB)
    pub.bind("tcp://*:7001")

    await asyncio.sleep(1)

    # print("Resetting simulation")
    # await pub.send_multipart([b"reset", b""])

    print("Running controller")
    x_prev = None
    t_prev = None
    try:
        while True:
            topic, msg = await sub.recv_multipart()
            if topic != b"output":
                continue

            data = json.loads(msg)
            t = data['t']
            x = data['x']



            # Implement controller code here
            dt = max(t - t_prev, 0.00001) if t_prev != None else 0.1
            print(dt)
            t_prev = t


            x_target = 0.0
            x_error = x_target - x
            x_dot = (x_prev - x)/dt if x_prev != None else 0.0
            x_prev = x

            u = (3.0 * x_error + 0.5 * x_dot)


            # Send data back to simulation
            await pub.send_multipart([b"input/u", f"{u}".encode("utf-8")])

    except Exception as e:
        print("Error with controller", e)
        print(traceback.format_exc())


if __name__=="__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(controller())
