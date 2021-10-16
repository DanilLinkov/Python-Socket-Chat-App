#!/usr/bin/env python3

import threading
import socket
import argparse
import os
import select
import sys
from ActionEnum import ActionType

from Utils import *


class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.clientsList = []

        self.groups = []

        self.host = host
        self.port = port

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

        self.server.listen(5)
        print('Server listening at', self.server.getsockname())

        self.inputs = [self.server]

    def run(self):
        while True:
            try:
                readable, writeable, exceptional = select.select(
                    self.inputs, [], [])
            except select.error as e:
                break

            for sock in readable:
                print(sock)
                sys.stdout.flush()

                # It will only ever be the server socket so no actuall need for this check
                if sock == self.server:
                    # Accept connection from user
                    client, address = self.server.accept()

                    # Receive name from client
                    clientName = receive(client)

                    print(
                        f'New user connection: Name: {clientName}, {client.fileno()} from {address}')

                    # Create new Server socket
                    newServerSocket = ServerSocket(
                        client, address, clientName + ":" + str(client.fileno()), self)
                    newServerSocket.start()

                    # Add it to the clients list
                    self.clientsList.append(newServerSocket)

                    # Broadcast to all the other users that a new client joined
                    self.updateConnectedClientsList()
                    self.sendMessageToAllClients(
                        (ActionType.createRoom, self.getListOfGroupsNames()))

    def removeClientFromClientsList(self, clientSocketToRemove):
        # Remove them from any group
        self.removeClientFromGroups(clientSocketToRemove)
        self.clientsList.remove(clientSocketToRemove)
        self.updateConnectedClientsList()

    def removeClientFromGroups(self, clientSocketToRemove):
        for i, group in enumerate(self.groups):
            if clientSocketToRemove in group[1]:
                print(clientSocketToRemove.clientName + " has left group " +
                      "Room "+str(i)+" by "+group[0].clientName)
                group[1].remove(clientSocketToRemove)
                self.sendMessageToGroup(
                    group, (ActionType.groupUsersListUpdate, self.getUserNamesListInGroup(group)))

    def updateConnectedClientsList(self):
        self.sendMessageToAllClients(
            (ActionType.allUsersListUpdate, self.getListOfNamesOfClients()))

    def getListOfNamesOfClients(self):
        names = []

        for client in self.clientsList:
            names.append(client.clientName)

        return names

    def sendMessageToAllClients(self, messageAsTuple):
        for client in self.clientsList:
            client.sendMessageToClient(messageAsTuple)

    def sendMessageToSingleClient(self, clientTo, messageAsTuple):
        for client in self.clientsList:
            if client.clientName == clientTo:
                client.sendMessageToClient(messageAsTuple)

    def getListOfGroupsNames(self):
        groupNames = []

        for i, group in enumerate(self.groups):
            groupNames.append(
                "Room "+str(i)+" by "+group[0].clientName)

        return groupNames

    def createNewRoom(self, owner):
        self.groups.append((owner, []))

        self.sendMessageToAllClients(
            (ActionType.createRoom, self.getListOfGroupsNames()))

    def getUserNamesListInGroup(self, group):
        names = []

        for i, client in enumerate(group[1]):
            names.append(client.clientName)

        return names

    def addUserToGroup(self, newUser, groupToJoin):
        for i, group in enumerate(self.groups):
            if groupToJoin == "Room "+str(i)+" by "+group[0].clientName:
                group[1].append(newUser)
                self.sendMessageToGroup(
                    group, (ActionType.groupUsersListUpdate, self.getUserNamesListInGroup(group)))

    def sendMessageToGroup(self, group, messageAsTuple):
        for i, client in enumerate(group[1]):
            client.sendMessageToClient(messageAsTuple)

    def findGroupByString(self, groupName):
        for i, group in enumerate(self.groups):
            if groupName == "Room "+str(i)+" by "+group[0].clientName:
                return group

        return None


class ServerSocket(threading.Thread):
    def __init__(self, client, address, clientName, serverInstance):
        super().__init__()
        self.client = client
        self.address = address
        self.clientName = clientName
        self.serverInstance = serverInstance

    def run(self):
        while True:
            messageFromClient = receive(self.client)
            print(messageFromClient)

            if messageFromClient:
                messageType = messageFromClient[0]

                if messageType == ActionType.sendMessage:
                    # Send message to the userTo
                    toUser = messageFromClient[1]
                    actualMessage = messageFromClient[2]

                    self.serverInstance.sendMessageToSingleClient(
                        toUser, (ActionType.receiveMessage, self.clientName, actualMessage))

                elif messageType == ActionType.createRoom:
                    # Create the room and let everyone know a room has been made
                    self.serverInstance.createNewRoom(self)

                elif messageType == ActionType.groupUserJoined:
                    # Add user to group and let everyone know a new user has joined the group
                    self.serverInstance.addUserToGroup(
                        self, messageFromClient[1])

                elif messageType == ActionType.sendGroup:
                    toGroup = messageFromClient[1]
                    actualMessage = messageFromClient[2]

                    group = self.serverInstance.findGroupByString(toGroup)
                    self.serverInstance.sendMessageToGroup(
                        group, (ActionType.receiveGroup, self.clientName, actualMessage))

                elif messageType == ActionType.invite:
                    toUser = messageFromClient[1]
                    toGroup = messageFromClient[2]

                    self.serverInstance.sendMessageToSingleClient(
                        toUser, (ActionType.invite, self.clientName, toGroup))

                elif messageType == ActionType.userQuitServer:
                    print(f'Client: {self.clientName} has disconected.')
                    self.serverInstance.removeClientFromClientsList(self)

                elif messageType == ActionType.userQuitGroup:
                    self.serverInstance.removeClientFromGroups(self)

            else:
                print(f'Client: {self.clientName} has closed the connection.')
                self.serverInstance.removeClientFromGroups(self)

    def sendMessageToClient(self, messageAsTuple):
        send(self.client, messageAsTuple)


if __name__ == "__main__":
    # Take input from console later
    server = Server("localhost", 9988)
    server.start()
