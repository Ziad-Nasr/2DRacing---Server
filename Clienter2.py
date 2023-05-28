import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
# accept all topics (prefixed) - default is none
socket.setsockopt(zmq.SUBSCRIBE, b"InGame")
socket.bind("tcp://*:7871")

while True:
    string = socket.recv()
    topic, message = string.split()
    print(topic, "and", message)
