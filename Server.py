#!/usr/bin/env python3

import threading
import socket
import argparse
import os
import select
import sys
import signal
import ssl
from ActionEnum import ActionType

from Utils import *

# Change this to change the server ip
SERVER_HOST = 'localhost'


class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()

        # List of ServerSocket objects
        self.clientsList = []

        # List of groups in the form of (owner,[users])
        self.groups = []

        self.host = host
        self.port = port

        # Adding encryption to the server
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.context.load_cert_chain(certfile="cert.pem", keyfile="cert.pem")
        self.context.load_verify_locations('cert.pem')
        self.context.set_ciphers('AES128-SHA')

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))

        self.server.listen(5)
        print('Server listening at', self.server.getsockname())

        self.server = self.context.wrap_socket(self.server, server_side=True)

        self.inputs = [self.server]

    def close(self,):
        # Close all the client sockets and close the server socket
        print('Shutting down server...')

        for client in self.clientsList:
            client.close()

        self.server.close()

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

                    # Create new Server socket which is a seperate thread for each new client that serves them
                    newServerSocket = ServerSocket(
                        client, address, clientName + ":" + str(client.fileno()), self)
                    newServerSocket.start()

                    # Add it to the clients list
                    self.clientsList.append(newServerSocket)

                    # Sends the clients name to them because the fileno() on the client side is different to the server one
                    # so I had to send it manually like this
                    newServerSocket.sendMessageToClient(
                        ("clientName", clientName + ":" + str(client.fileno())))

                    # Broadcast to all the other users that a new client joined
                    self.updateConnectedClientsList()

                    # Send a list of rooms to the new user that joined
                    # Slighly a hack since it actually sends it to all the users
                    self.sendMessageToAllClients(
                        (ActionType.createRoom, self.getListOfGroupsNames()))

    def removeClientFromClientsList(self, clientSocketToRemove):
        # Remove them from any group
        self.removeClientFromGroups(clientSocketToRemove)

        # Remove them from the client list
        self.clientsList.remove(clientSocketToRemove)

        # Let the other users know
        self.updateConnectedClientsList()

    def removeClientFromGroups(self, clientSocketToRemove):
        # Go over every group and find the group that the client socket is part of
        for i, group in enumerate(self.groups):
            if clientSocketToRemove in group[1]:
                print(clientSocketToRemove.clientName + " has left group " +
                      "Room "+str(i)+" by "+group[0].clientName)
                # Remove them
                group[1].remove(clientSocketToRemove)
                # Let the people in the group know that the user left
                self.sendMessageToGroup(
                    group, (ActionType.groupUsersListUpdate, self.getUserNamesListInGroup(group)))

    def updateConnectedClientsList(self):
        # Send a list of all the clients connected to the server to all the clients
        self.sendMessageToAllClients(
            (ActionType.allUsersListUpdate, self.getListOfNamesOfClients()))

    def getListOfNamesOfClients(self):
        names = []

        # Loop over every server socket and get its client name
        for client in self.clientsList:
            names.append(client.clientName)

        return names

    def sendMessageToAllClients(self, messageAsTuple):
        # Go over every client socket and send them the message tuple
        for client in self.clientsList:
            client.sendMessageToClient(messageAsTuple)

    def sendMessageToSingleClient(self, clientTo, messageAsTuple):
        # Find the client socket that has the same name as the clientTo
        for client in self.clientsList:
            if client.clientName == clientTo:
                client.sendMessageToClient(messageAsTuple)

    def getListOfGroupsNames(self):
        groupNames = []

        # Goes over the list of groups and formats the name accordingly to be sent to all the clients
        for i, group in enumerate(self.groups):
            groupNames.append(
                "Room "+str(i)+" by "+group[0].clientName)

        return groupNames

    def createNewRoom(self, owner):
        # Add the new group to the groups list and let all the clients know
        self.groups.append((owner, []))

        self.sendMessageToAllClients(
            (ActionType.createRoom, self.getListOfGroupsNames()))

    def getUserNamesListInGroup(self, group):
        names = []

        # Goes over every ServerSocket object connected to the group and gets their name
        for i, client in enumerate(group[1]):
            names.append(client.clientName)

        return names

    def addUserToGroup(self, newUser, groupToJoin):
        # Finds the group the user wants to join to and adds them to the list
        for i, group in enumerate(self.groups):
            if groupToJoin == "Room "+str(i)+" by "+group[0].clientName:
                group[1].append(newUser)
                self.sendMessageToGroup(
                    group, (ActionType.groupUsersListUpdate, self.getUserNamesListInGroup(group)))

    def sendMessageToGroup(self, group, messageAsTuple):
        # Sends a message tuple to all the ServerSocket objects in the group list
        for i, client in enumerate(group[1]):
            client.sendMessageToClient(messageAsTuple)

    def findGroupByString(self, groupName):
        # Finds a group from the list by name
        for i, group in enumerate(self.groups):
            if groupName == "Room "+str(i)+" by "+group[0].clientName:
                return group

        return None


# Seperate thread class that handles each client that wants to connect
class ServerSocket(threading.Thread):
    def __init__(self, client, address, clientName, serverInstance):
        super().__init__()
        self.client = client
        self.address = address
        self.clientName = clientName
        self.serverInstance = serverInstance

    def close(self):
        self.client.close()

    def run(self):
        while True:
            try:
                # Receive message from client to be inspected
                messageFromClient = receive(self.client)
                print(messageFromClient)

                if messageFromClient:
                    # Message type is a tuple from ActionEnum.py
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
                        # Send the message to each user in that group
                        toGroup = messageFromClient[1]
                        actualMessage = messageFromClient[2]

                        group = self.serverInstance.findGroupByString(toGroup)
                        self.serverInstance.sendMessageToGroup(
                            group, (ActionType.receiveGroup, self.clientName, actualMessage))

                    elif messageType == ActionType.invite:
                        # Send an invite request to a user
                        toUser = messageFromClient[1]
                        toGroup = messageFromClient[2]

                        self.serverInstance.sendMessageToSingleClient(
                            toUser, (ActionType.invite, self.clientName, toGroup))

                    elif messageType == ActionType.userQuitServer:
                        # If a user clicks close on the connected screen they are disconnected from the server
                        print(f'Client: {self.clientName} has disconected.')
                        self.serverInstance.removeClientFromClientsList(self)

                    elif messageType == ActionType.userQuitGroup:
                        # User clicked close on the group and therefore this is sent to the server to remove them from the group
                        # and let the other users know they left the group
                        self.serverInstance.removeClientFromGroups(self)

                else:
                    print(
                        f'Client: {self.clientName} has closed the connection.')
                    self.serverInstance.removeClientFromGroups(self)
            except:
                pass

    def sendMessageToClient(self, messageAsTuple):
        send(self.client, messageAsTuple)


def exit(server):
    while True:
        ipt = input('Type q to quit\n')
        if ipt == 'q':
            print('Closing all connections...')
            server.close()
            print('Shutting down the server...')

            os._exit(0)


if __name__ == "__main__":
    # Take input from console later
    parser = argparse.ArgumentParser(
        description='Socket Server Example with Select')
    parser.add_argument('--port', action="store",
                        dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port

    server = Server(SERVER_HOST, port)
    server.start()

    exit = threading.Thread(target=exit, args=(server,))
    exit.start()
