import zmq


context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")

topic = "data".encode("utf-8")
socket.setsockopt(zmq.SUBSCRIBE, topic)

try:
    while True:
        topic, msg = socket.recv_multipart()
        print(f"Topic: {topic}\nMessage: {msg}")
except KeyboardInterrupt:
    pass

print("Done")


