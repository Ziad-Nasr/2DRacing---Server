import zmq

PORT = "7878"

context = zmq.Context()
socket = context.socket(zmq.SUB)
# accept all topics (prefixed) - default is none
socket.setsockopt(zmq.SUBSCRIBE, b"15")
socket.bind("tcp://*:%s" % PORT)

while True:
    string = socket.recv_string()
    print(string)
