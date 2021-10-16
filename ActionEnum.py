import enum


class ActionType(enum.Enum):
    joined = 1
    left = 2
    sendMessage = 3
    receiveMessage = 4
    sendGroup = 5
    receiveGroup = 6
    allUsersListUpdate = 7
    groupUsersListUpdate = 8
    invite = 9
    groupUserJoined = 10
    createRoom = 11
    userQuitServer = 12
    userQuitGroup = 13
