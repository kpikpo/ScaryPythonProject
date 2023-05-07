import logging
import socket
import time
import traceback

import select
from PyQt6 import QtCore
from PyQt6.QtCore import QObject, pyqtSignal

from net.message_parser import MessageParser


class ChatSocketWorker(QObject):
    MAX_CONNECTION_RETRIES = 5
    RETRY_AFTER_SECONDS = 3

    message_received = pyqtSignal(str, object, bytearray)
    on_connected = pyqtSignal()
    on_connection_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.port = None
        self.host = None
        self.failed_connections = 0
        self.sock = socket.socket()
        self.start_poll_timer = QtCore.QTimer()
        self.connection_retry_timer = QtCore.QTimer()

    def connect(self, host, port):
        self.host = host
        self.port = port
        self.connection_retry_timer.stop()

        try:
            self.sock.close()
            self.sock = socket.socket()
            self.sock.settimeout(1)
            self.sock.connect((host, port))
            self.on_connected.emit()
        except Exception as e:
            self.on_connection_error.emit("Couldn't connect to the server.")
            logging.critical(traceback.format_exc())
            self.try_reconnect()
            return

        logging.info("Connected to the server successfully.")

        # Hacky workaround to avoid it blocking the thread
        self.start_poll_timer = QtCore.QTimer()
        self.start_poll_timer.setSingleShot(True)
        self.start_poll_timer.timeout.connect(self.poll)
        self.start_poll_timer.start(5)

    def try_reconnect(self):
        # Already trying to connect - ignore
        if self.connection_retry_timer.isActive():
            return

        self.on_connection_error.emit(f"Retrying to connect in {self.RETRY_AFTER_SECONDS} seconds ...")
        self.connection_retry_timer = QtCore.QTimer()
        self.connection_retry_timer.timeout.connect(lambda: self.connect(self.host, self.port))
        self.connection_retry_timer.setSingleShot(True)
        self.connection_retry_timer.start(self.RETRY_AFTER_SECONDS * 1000)

    def poll(self):
        logging.info("Starting to poll incoming messages.")
        parser = MessageParser()
        while True:
            rdata = b""

            ready_to_read, _, err = select.select([self.sock], [self.sock], [self.sock], 1)

            if len(err) != 0:
                self.on_connection_error.emit("Couldn't get incoming messages: Connection error.")
                self.try_reconnect()
                return

            try:
                for r in ready_to_read:
                    rdata += r.recv(2**16)
                    print("Received", rdata)

                    if len(rdata) == 0:
                        raise ConnectionError

                    parser.add_bytes(rdata)
            except (ConnectionResetError, ConnectionAbortedError, ConnectionError) as e:
                self.on_connection_error.emit("Couldn't get incoming messages: Connection to the server was lost.")
                logging.critical(traceback.format_exc())
                self.try_reconnect()
                return

            for msg_type, msg_display, msg_raw in parser.consume_messages():
                self.message_received.emit(msg_type, msg_display, msg_raw)

            time.sleep(0.1)

    def send_message(self, data: bytearray):
        try:
            self.sock.send(data)
            logging.info(f"Sent message: \n{data}\n")
        except (ConnectionResetError, ConnectionAbortedError, ConnectionError) as e:
            self.on_connection_error.emit("Couldn't send message: Connection to the server was lost.")
            self.try_reconnect()
            logging.critical(traceback.format_exc())
