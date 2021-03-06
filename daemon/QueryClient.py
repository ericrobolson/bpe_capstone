#!/usr/bin/python3.3
#
#  File:    QueryClient.py
#  Author:  Daniel E. Wilson
#
#  File of classes to handle the queries in the backend of
#  the BPA database.
#
#  Bonneville Power Adminstration Front-End
#  Copyright (C) 2015 Daniel E. Wilson.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, US$
#
import queue
import threading
import time
import socket
import json

# Set the host name and port number of the database engine.
host = 'localhost'
port = 1701

# Set the default time limit
timeLimit = 5 * 60


class QueryEngine(threading.Thread):
    "Class that handles all of the queries to the BPA engine"

    def __init__(self, dataEngine):
        threading.Thread.__init__(self, None, self.run)
        self.dataEngine = dataEngine
        self.daemon = True
        self.queue = Queue.Queue(25)
        self.client = BPAClient(host, port)
        self.lastHour = None

    def putQuery(self, query):
        "Add the query to the queue."
        self.queue.put(query, True, None)

    def run(self):
        "Start the server task."
        while True:
            # Get list of signals after midnight and store in database.
            if self.afterMidnight():
                signals = self.client.getSignals()
                dataEngine.addSignals(signals['PMUs'], signals['Signals'])

            # Get the next query from the queue.
            try:
                query = self.queue.get(True, timeLimit)

            # Query the BPA server if wait time exceeded.
            except Queue.Empty:
                currentStatus = self.client.getQueryStatus()

            else:
                # Submit the query to the BPA server.
                result = self.client.startQuery(query)

                # Write the query results to the database.
                responseLists = result['Status']
                dataEngine.updateStatus(responseLists['QueryResponses'],
                                        responseLists['AnalysisResponses'],
                                        responseLists['QueryStatus'],
                                        responseLists['StatusResponses'])

                # Mark the current item as complete.
                self.queue.task_done()

                # Create new BPA client object.
                self.client = BPAClient(host, port)


    def afterMidnight(self):
        "Check to see if midnight has passed."
        if self.lastHour == None:
            now = time.localtime()
            self.lastHour = now.tm_hour
            status = False
        else:
            now = time.localtime()
            hour = now.tm_hour
            status = hour < self.lastHour
            self.lastHour = hour
        return status


class BPAClient:
    """Class that will handle communication with the BPA database.
NOTE:  This class can only handle one request per instance."""

    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.file = self.socket.makefile('rw', 4096, encoding='ascii')

    def sendJSON(self, msg):
        "Send a JSON message to the server."
        assert type(msg)==type({})
        json.dump(msg, self.file)
        self.file.write('\n\n')
        self.file.flush()

    def getJSON(self):
        "Get a JSON message from the server."
        result = json.load(self.file)
        ignore = self.file.readline()
        return result

    def getQueryStatus(self):
        "Get the status of all running queries from the BPA server."
        self.sendJSON({"StatusRequest": ["Status", "Results", "Analysis"]})
        result = self.getJSON()
        return result

    def startQuery(self, query):
        "Start a new query on the BPA server."
        assert type(query)==type({})

        # Send the query request to the server.
        self.sendJSON(query)

        # Read the result from the server.
        result = self.getJSON()
        return result

    def getSignals(self):
        "Get the signals from the BPA Server."
        # Send the signal request.
        self.sendJSON({'PMUAndSignalRequest' : 0})

        # Get the signal list from the server.
        result = self.getJSON()
        return result

    def __del__(self):
        "Clean up the socket and file descriptors."
        # Clean up the file if it exists.
        try:
            self.rfile.close()
        except AttributeError:
            pass

        # Clean up the socket if it exists.
        try:
            self.socket.close()
        except AttributeError:
            pass
