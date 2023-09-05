import time
import zmq


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")
topic = "data".encode("utf-8")

counter = 0
while True:
    message = f"Hello({counter})".encode("utf-8")
    print("Sending: %s" % message)
    socket.send_multipart([topic, message])


    time.sleep(1)
    counter += 1



