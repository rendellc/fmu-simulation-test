import asyncio
import zmq
import zmq.asyncio
import time
import sys
from multiprocessing import Process

async def publisher(address:str, topic:str):
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(address)
    topic = topic.encode("utf-8")

    counter = 0.0
    for i in range(10):
        message = f"{counter}".encode("utf-8")
        print("Sending: %s" % message)
        await socket.send_multipart([topic, message])

        time.sleep(1)
        counter += 1

async def subscriber(address:str, topic: str, callback):
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(address)
    socket.setsockopt(zmq.SUBSCRIBE, topic.encode("utf-8"))


    try:
        for i in range(5):
            topic, msg = await socket.recv_multipart()
            print(f"Topic: {topic}\nMessage: {msg}")
            callback(msg)
    except KeyboardInterrupt:
        pass


def on_u_changed(u):
    print("on_u_changed:", u)


async def main():
    await asyncio.gather(
        publisher("tcp://*:5555", "u"),
        subscriber("tcp://localhost:5555", "u", on_u_changed),
    )

if __name__=="__main__":
    asyncio.run(main())






