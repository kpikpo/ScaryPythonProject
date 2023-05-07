import sys

from PyQt6 import QtWidgets
from PyQt6.QtCore import QThread

# Needed for static resources - don't remove even if we don't directly reference this
# noinspection PyUnresolvedReferences
import res.ui.imgs_rc
from net.chat_socket_worker import ChatSocketWorker
from ui.chat_window import ChatWindow


class ChatApp(QtWidgets.QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        self.window = ChatWindow()
        self.window.show()

        host = "vlbelintrocrypto.hevs.ch"
        port = 6000

        self.worker = ChatSocketWorker()
        self.thread = QThread()
        self.window.message_sent.connect(self.worker.send_message)
        self.worker.message_received.connect(self.window.receive_message)
        self.worker.on_connected.connect(self.window.on_socket_connected)
        self.worker.on_connection_error.connect(self.window.on_socket_connection_error)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(lambda: self.worker.connect(host, port))
        self.thread.start()
        self.window.connect_to_server = lambda h, p: self.worker.connect(h, p)

