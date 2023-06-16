import zmq
import time
import pickle
from threading import Thread
import requests
import json


class Server:
    # MY OWN IP ADDRESS
    IP = "178.79.133.165"
    # server ips
    AUTH_SERVER = "178.79.139.125"
    localhost = "127.0.0.1"

    # ports
    pub_PORT = "7878" # publisher port
    pull_PORT = "8787" # recieve port
    rep_PORT = "12345" # server port

    # message constants
    GetState = "GS"
    SingleState = "SS"
    ChangeCoordinates = "G"
    Ready = "R"
    Join = "J"
    NewChatMessage = "C"

    # games data
    Data = []

    # sockets
    pub_socket = None
    pull_socket = None
    rep_socket = None
    
    
    def __init__(self):
        # =========================================
        # Example Structrue
        #self.Data = [
        #    {
        #        "GameID": 1,
        #        "state": "starting" | "ongoing" | "done",
        #        "other_tracker": "0.0.0.0",
        #        "Players_Info": [{
        #            "ID": "ziad",
        #            "Position_X": 0,
        #            "Position_Y": 0
        #            "Ready": 0
        #        },
        #        {
        #            "ID": "osos",
        #            "Position_X": 0,
        #            "Position_Y": 0
        #            "Ready": 0
        #        },
        #        {
        #            "ID": "hawary",
        #            "Position_X": 0,
        #            "Position_Y": 0
        #            "Ready": 0
        #        }
        #        ]
        #    }
        #]
        # =========================================
        self.context = zmq.Context()
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind("tcp://%s:%s" % (self.IP, self.pub_PORT))
        self.pull_socket = self.context.socket(zmq.PULL)
        self.pull_socket.bind("tcp://%s:%s" % (self.IP, self.pull_PORT))
        self.rep_socket = self.context.socket(zmq.REP)
        self.rep_socket.bind("tcp://%s:%s" % (self.IP, self.rep_PORT))
    # Message: GAME_ID PLAYER_ID TYPE DATA
    # Message: 1 hawary C Alooooooo ya geda3an
    # Message: 1 ziad G LEFT


    def getGameIdx(self, game_id):
        # Looping to determine which GameID to edit upon
        Selected_Game_ID = -1
        for Game in self.Data:
            if (Game["GameID"] == game_id):
                Selected_Game_ID = self.Data.index(Game)
        return Selected_Game_ID


    def getPlayerIdx(self,game_idx,  player_id):
        Selected_Player = -1
        for Player in self.Data[game_idx]["Players_Info"]:
            if (Player["ID"] == player_id):
                Selected_Player = self.Data[game_idx]["Players_Info"].index(Player)
        return Selected_Player
    
    
    def ChangeCordinatesRequest(self, Player_ID, Game_ID, Direction):
        Selected_Game_ID = self.getGameIdx(Game_ID)
        Selected_Player = self.getPlayerIdx(Selected_Game_ID, Player_ID)
        if (Direction == "UP"):
            self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"] += 1
        elif (Direction == "RIGHT"):
            self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"] += 1
        elif (Direction == "LEFT"):
            self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"] -= 1

        if self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"] >= 100:
            msg = "%s STOP" % (Game_ID)
            self.pub_socket.send_string(msg)
            self.pushToTracker(self.Data[Selected_Game_ID]["Other_Tracker"], msg)
            self.Data[Selected_Game_ID]["Status"] = "Done"
            res = requests.post("http://"+self.AUTH_SERVER+":5000/done", data={"game_id": Game_ID})
            return

        msg = "%s %s G %s %s" % (Game_ID, Player_ID, str(self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"]), str(self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"]))
        other_tracker_msg = "%s %s SSG %s %s" % (Game_ID, Player_ID, str(self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"]), str(self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"]))
        print("sending: " + msg)
        self.pub_socket.send_string(msg)
        self.pushToTracker(self.Data[Selected_Game_ID]["Other_Tracker"], other_tracker_msg)
    

    def NewGame(self,Game_ID, other_tracker):
        print("Added Game %s With tracker %s" % (Game_ID, other_tracker))
        self.Data.append({"GameID": Game_ID, "Status":"Starting", "Other_Tracker": other_tracker, "Players_Info": []})
    
    
    def NewPlayer(self, Player_ID, Game_ID):
        Selected_GameID = self.getGameIdx(Game_ID)
        x = (len(self.Data[Selected_GameID]["Players_Info"]) % 5) + 1
        y = len(self.Data[Selected_GameID]) // 5
        self.Data[Selected_GameID]["Players_Info"].append({"ID": Player_ID, "Position_X": x, "Position_Y": y, "Ready": 0})
        msg = "%s %s J %s %s" % (Game_ID, Player_ID, x, y)
        print("PUBLISHING " + msg)
        self.pub_socket.send_string(msg)
        other_tracker_msg = "%s %s SSJ" % (Game_ID, Player_ID)
        self.pushToTracker(self.Data[Selected_GameID]["Other_Tracker"], other_tracker_msg)

    def ReadyPlayer(self, Player_ID, Game_ID):
        Selected_Game_ID = self.getGameIdx(Game_ID)
        Selected_Player = self.getPlayerIdx(Selected_Game_ID, Player_ID)
        self.Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Ready"] = 1
        msg = "%s %s R" % (Game_ID, Player_ID)
        other_tracker_msg = "%s %s SSR" % (Game_ID, Player_ID)
        self.pub_socket.send_string(msg)
        self.pushToTracker(self.Data[Selected_Game_ID]["Other_Tracker"], other_tracker_msg)

        # if all players are ready, send start game Message
        sendStart = True
        for player in self.Data[Selected_Game_ID]["Players_Info"]:
            if player["Ready"] == 0:
                sendStart = False
                break
        if sendStart:
            print("Sending Start Message")
            self.Data[Selected_Game_ID]["Status"] = "Ongoing"
            self.pub_socket.send_string("%s START" % Game_ID)
            self.pushToTracker(self.Data[Selected_Game_ID]["Other_Tracker"], "%s START" % Game_ID)


    def listen_for_pipeline(self):
        print("listenening for pull..")
        while True:
            msg = self.pull_socket.recv()
            print("pipeline")
            print(msg)
            data = msg.decode().split()
            game_id = data[0]
            player_id = data[1]
            if data[1] == "START":
                game_idx = self.getGameIdx(game_id)
                self.Data[game_idx]["Status"] = "Ongoing"
            elif data[1] == "STOP":
                game_idx = self.getGameIdx(game_id)
                self.Data[game_idx]["Status"] = "Done"
            if len(data) > 2:
                if data[2] == self.NewChatMessage:
                    print("pushing back")
                    self.pub_socket.send(msg)
                elif data[2] == self.ChangeCoordinates:
                    self.ChangeCordinatesRequest(player_id, game_id, data[3])
                elif data[2] == self.Join:
                    self.NewPlayer(player_id, game_id)
                elif data[2] == self.Ready:
                    self.ReadyPlayer(player_id, game_id)
                elif data[2] == "SG":
                    self.NewGame(game_id, data[3])
                elif data[2] == self.SingleState+self.ChangeCoordinates: # game_id player_id SSG x y
                    x = data[3]
                    y = data[4]
                    game_idx = self.getGameIdx(game_id)
                    player_idx = self.getPlayerIdx(game_idx, player_id)
                    self.Data[game_idx]["Players_Info"][player_idx]["Position_X"] = int(x)
                    self.Data[game_idx]["Players_Info"][player_idx]["Position_Y"] = int(y)
                elif data[2] == self.SingleState+self.Join: # game_id player_id SSJ
                    game_idx = self.getGameIdx(game_id)
                    self.Data[game_idx]["Players_Info"].append({"ID": player_id, "Position_X": 0, "Position_Y": 0, "Ready": 0})
                elif data[2] == self.SingleState+self.Ready: # game_id player_id SSR
                    game_idx = self.getGameIdx(game_id)
                    player_idx = self.getPlayerIdx(game_idx, player_id)
                    self.Data[game_idx]["Players_Info"][player_idx]["Ready"] = 1


    def listen_for_reply(self):
        print("listening for reply..")
        while True:
            msg = self.rep_socket.recv().decode()
            print("req/rep")
            print(msg)
            data = msg.split(" ")
            game_id = data[0]
            msg_type = data[1]
            if len(data) > 2:
                data = data[2:]
            print(msg_type)
            if msg_type == self.GetState:
                print("sending back")
                game_idx = self.getGameIdx(game_id)
                self.rep_socket.send(pickle.dumps(self.Data[game_idx]))


    def pushToTracker(self, tracker, msg):
        s = self.context.socket(zmq.PUSH)
        s.connect("tcp://%s:%s" % (tracker, self.pull_PORT))
        s.send_string(msg)


    def getGame(self, game_id, tracker):
        s = self.context.socket(zmq.REQ)
        s.connect("tcp://%s:%s" % (tracker, self.rep_PORT))
        s.send_string(str(game_id) + " " + self.GetState)
        game = pickle.loads(s.recv())
        self.Data.append(game)


    def getMyGames(self):
        res = requests.post("http://"+self.AUTH_SERVER+":5000/list_tracker_games", data={"ip": self.IP})
        games = json.loads(res.text)
        for game in games:
            game_id = game[0]
            tracker_1 = game[3]
            tracker_2 = game[4]
            if tracker_1 == self.IP:
                self.getGame(game_id, tracker_2)
            else:
                self.getGame(game_id, tracker_1)

    def start(self):
        t1 = Thread(target=self.listen_for_pipeline)
        t2 = Thread(target=self.listen_for_reply)
        self.getMyGames()
        t1.start()
        t2.start()

if __name__ == "__main__":
    server = Server()
    server.start()
