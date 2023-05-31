import zmq
import time
import pickle
from threading import Thread


class Server:
    localhost = "127.0.0.1"
    pub_PORT = "7878" # publisher port
    pull_PORT = "8787" # recieve port
    rep_PORT = "12345" # server port
    GetState = "GS"
    ChangeCoordinates = "G"
    NewChatMessage = "C"
    Data = []
    pub_socket = None
    pull_socket = None
    rep_socket = None
    
    
    def __init__(self):
        # =========================================
        # To be switched to Redis
        self.Data = [
            {
                "GameID": 1,
                "Players_Info": [{
                    "ID": "ziad",
                    "Position_X": 0,
                    "Position_Y": 0
                },
                {
                    "ID": "osos",
                    "Position_X": 0,
                    "Position_Y": 0
                },
                {
                    "ID": "hawary",
                    "Position_X": 0,
                    "Position_Y": 0
                }
                ]
            }
        ]
        context = zmq.Context()
        self.pub_socket = context.socket(zmq.PUB)
        self.pub_socket.bind("tcp://%s:%s" % (self.localhost, self.pub_PORT))
        self.pull_socket = context.socket(zmq.PULL)
        self.pull_socket.bind("tcp://%s:%s" % (self.localhost, self.pull_PORT))
        self.rep_socket = context.socket(zmq.REP)
        self.rep_socket.bind("tcp://%s:%s" % (self.localhost, self.rep_PORT))
        # open server ports
    # To be switched to Redis
    # =========================================
    # Message: GAME_ID TYPE PLAYER_ID DATA
    # Message: 1 C hawary Alooooooo ya geda3an
    # Message: 1 G ziad LEFT

    def getGameIdx(self, game_id):
        # Looping to determine which GameID to edit upon
        Selected_Game_ID = -1
        for Game in self.Data:
            if (Game["GameID"] == game_id):
                Selected_Game_ID = self.Data.index(Game)
        return Selected_Game_ID
    
    
    def ChangeCordinatesRequest(self, Player_ID, Game_ID, Direction):
        Selected_Game_ID = self.getGameIdx(Game_ID)

        # Looping to Determine Which Player to Edit Upon
        # Data[Game][Players_Info][Player][Player Attributes]
        Selected_Player = -1
        for Player in self.Data[Selected_Game_ID]["Players_Info"]:
            if (Player["ID"] == Player_ID):
                Selected_Player = self.Data[Selected_Game_ID]["Players_Info"].index(
                    Player)
        if (Direction == "UP"):
            self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"] += 1
        elif (Direction == "RIGHT"):
            self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"] += 1
        elif (Direction == "LEFT"):
            self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"] -= 1
        msg = "%s %s G %s %s" % (Game_ID, Player_ID, str(self.Data[Selected_Game_ID]["Players_Info"]
                [Selected_Player]["Position_X"]), str(self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"]))
        print("sending: " + msg)
        self.pub_socket.send_string(msg)
    

    def NewGame(self,Game_ID):
        self.Data.append({"GameID": Game_ID, "Players_Info": []})
    
    
    def NewPlayer(self, Player_Name, Player_ID, Game_ID):
        Selected_GameID = 0
        for item in Data:
            if (item["GameID"] == Game_ID):
                Selected_GameID = self.Data.index(item)
        print(Selected_GameID)
        self.Data[Selected_GameID]["Players_Info"].append(
            {"Name": Player_Name, "ID": Player_ID, "Position_X": 0, "Position_Y": 0})

    def listen_for_pipeline(self):
        print("listenening for pull..")
        while True:
            msg = self.pull_socket.recv()
            print("pipeline")
            print(msg)
            data = msg.decode().split()
            if data[2] == self.NewChatMessage:
                print("pushing back")
                self.pub_socket.send(msg)
            elif data[2] == self.ChangeCoordinates:
                self.ChangeCordinatesRequest(data[1], data[0], data[3])

    def listen_for_reply(self):
        print("listening for reply..")
        while True:
            msg = self.rep_socket.recv().decode()
            print("req/rep")
            print(msg)
            game_id, msg_type = msg.split(" ")
            print(msg_type)
            if msg_type == self.GetState:
                print("sending back")
                game_idx = self.getGameIdx(game_id)
                self.rep_socket.send(pickle.dumps(self.Data[game_idx]))

    def start(self):
        t1 = Thread(target=self.listen_for_pipeline)
        t2 = Thread(target=self.listen_for_reply)
        t1.start()
        t2.start()

if __name__ == "__main__":
    server = Server()
    server.start()
