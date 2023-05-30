import zmq
import time

localhost = "10.152.107.121"
PORT = "7878"
ChangeCoordinates = "Coordinates"
NewChatMessage = "Chat"


def ChangeCordinatesRequest(Player_ID, Game_ID, Direction):
    Selected_Game_ID = 0  # Used to change the variable scope

    # Looping to determine which GameID to edit upon
    for Game in Data:
        if (Game["GameID"] == Game_ID):
            Selected_Game_ID = Data.index(Game)

    # Looping to Determine Which Player to Edit Upon
    # Data[Game][Players_Info][Player][Player Attributes]
    for Player in Data[Selected_Game_ID]["Players_Info"]:
        print(Player)
        if (Player["ID"] == Player_ID):
            Selected_Player = Data[Selected_Game_ID]["Players_Info"].index(
                Player)
    if (Direction == "UP"):
        Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"] += 1
    elif (Direction == "RIGHT"):
        Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"] += 1
    elif (Direction == "LEFT"):
        Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_X"] -= 1
    Publish(ChangeCoordinates, "%s %s %s %s" % (Game_ID, Player_ID, Data[Selected_Game_ID]["Players_Info"]
            [Selected_Player]["Position_X"], Data[Selected_Game_ID]["Players_Info"][Selected_Player]["Position_Y"]))


def Publish(Type, Message):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.connect("tcp://%s:%s" % (localhost, PORT))
    time.sleep(1)
    for i in range(2):
        if (Type == ChangeCoordinates):
            print("G "+Message)
            socket.send_string("G " + Message)
        elif (Type == NewChatMessage):
            socket.send_string("C " + Message)
        time.sleep(1)


def NewGame(Game_ID):
    Data.append({"GameID": Game_ID, "Players_Info": []})


def NewPlayer(Player_Name, Player_ID, Game_ID):
    Selected_GameID = 0
    for item in Data:
        if (item["GameID"] == Game_ID):
            Selected_GameID = Data.index(item)
    print(Selected_GameID)
    Data[Selected_GameID]["Players_Info"].append(
        {"Name": Player_Name, "ID": Player_ID, "Position_X": 0, "Position_Y": 0})


# =========================================
# To be switched to Redis
Data = [
    {
        "GameID": 1,
        "Players_Info": [{
            "Name": "Ziad",
            "ID": 1,
            "Position_X": 0,
            "Position_Y": 0
        },
            {
            "Name": "OSOS",
            "ID": 2
        }
        ]
    }
]
# To be switched to Redis
# =========================================


# print(Data)
# NewGame(4)
# print(Data)
# NewPlayer("Ziad", 12, 4)
# print(Data)
# Data[0]["Data"].append({"Tester": 2})
# print(Data[0]["Data"])
# myList.append({"Name": "Hawary", "ID": 3})
# print(myList)
# NewPlayer("Hawary", 3, 0)
# ChangeCordinatesRequest(12, 4, "UP")
# print(Data)
