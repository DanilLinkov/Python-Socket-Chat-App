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
        self.numOfClients = 0
        self.clientsList = []
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
                        client, address, clientName, self)
                    newServerSocket.start()

                    # Add it to the clients list
                    self.clientsList.append(newServerSocket)

                    # Broadcast to all the other users that a new client joined
                    self.updateConnectedClientsList()

    def removeClientFromClientsList(self, clientSocketToRemove):
        self.clientsList.remove(clientSocketToRemove)
        self.updateConnectedClientsList()

    def updateConnectedClientsList(self):
        self.sendMessageToAllClients(
            (ActionType.allUsersListUpdate, self.getListOfNamesOfClients()))

    def getListOfNamesOfClients(self):
        names = []

        for client in self.clientsList:
            names.append(client.clientName+":" +
                         str(self.clientsList.index(client)))

        return names

    def sendMessageToAllClients(self, messageAsTuple):
        for client in self.clientsList:
            client.sendMessageToClient(messageAsTuple)

    def sendMessageToSingleClient(self, clientTo, messageAsTuple):
        for client in self.clientsList:
            print(client.clientName)
            if client.clientName == clientTo:
                client.sendMessageToClient(messageAsTuple)


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
                    toUser = messageFromClient[1].split(":")[0]
                    actualMessage = messageFromClient[2]

                    self.serverInstance.sendMessageToSingleClient(
                        toUser, (ActionType.receiveMessage, self.clientName+":"+str(self.serverInstance.clientsList.index(self)), actualMessage))
            else:
                print(f'Client: {self.clientName} has disconected.')
                self.serverInstance.removeClientFromClientsList(self)

    def sendMessageToClient(self, messageAsTuple):
        send(self.client, messageAsTuple)


if __name__ == "__main__":
    # Take input from console later
    server = Server("localhost", 9988)
    server.start()
