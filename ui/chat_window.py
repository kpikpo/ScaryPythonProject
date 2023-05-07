import binascii
import re
from array import array
from time import localtime, strftime

from PyQt6 import QtWidgets, uic, QtGui, QtCore
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QLineEdit, QSpinBox, QPushButton, QPlainTextEdit, QScrollArea, \
    QLabel

from crypto.diffie_hellman import difhel_generate_space, difhel_shared_secret
from crypto.rsa import rsa_keygen, rsa_encode, rsa_decode
from crypto.vigenere_shift import vigenere_encode, numerical_encode, numerical_decode, vigenere_decode
from crypto.hashing import hash_int_array, hash_str
from net.message_builder import build_text_message, build_image_message, build_text_message_intarray, str_to_intarray


class ChatWindow(QtWidgets.QMainWindow):
    # Emitted when a message has been sent by the user
    message_sent = pyqtSignal(bytearray)

    def __init__(self):
        super().__init__()

        uic.loadUi("res/ui/chat_window.ui", self)
        self.setWindowTitle("ISC Chat")
        self.setAcceptDrops(True)

        self.text_messages = []

        # Whether the messages box should scroll down to display new messages
        self.scroll_follow_new = True
        self.last_sent_server_message = None

        self.messages_box = self.findChild(QtWidgets.QVBoxLayout, "messages_box")

        # Align messages from the top
        self.messages_box.layout().setAlignment(Qt.AlignmentFlag.AlignTop)

        self.message_input: QtWidgets.QPlainTextEdit = self.findChild(QtWidgets.QPlainTextEdit, "message_input")
        self.message_input.installEventFilter(self)
        #self.message_input.returnPressed.connect(self.send_text_message)

        self.send_button = self.findChild(QPushButton, "send_button")
        self.send_button.clicked.connect(self.send_text_message)

        self.attach_image_button = self.findChild(QPushButton, "attach_image_button")
        self.attach_image_button.clicked.connect(self.open_image_picker)

        self.messages_scroll_area: QScrollArea = self.findChild(QtWidgets.QScrollArea, "messages_scroll_area")
        self.messages_scroll_area.horizontalScrollBar().setEnabled(False)
        self.vertical_scroll_bar = self.messages_scroll_area.verticalScrollBar()
        self.vertical_scroll_bar.rangeChanged.connect(self.update_scroll)
        self.vertical_scroll_bar.valueChanged.connect(self.update_scroll_follow_new)

        self.trans_input: QPlainTextEdit = self.findChild(QtWidgets.QPlainTextEdit, "plainTextEdit_trans_input")

        self.shift_key_input: QSpinBox = self.findChild(QtWidgets.QSpinBox, "numshift_key")
        self.shift_encode_btn = self.findChild(QPushButton, "numshift_encode")
        self.shift_encode_btn.clicked.connect(lambda: self.do_shift(numerical_encode, self.shift_key_input))
        self.shift_decode_btn = self.findChild(QPushButton, "numshift_decode")
        self.shift_decode_btn.clicked.connect(lambda: self.do_shift(numerical_decode, self.shift_key_input))

        self.vigenere_key_input: QLineEdit = self.findChild(QtWidgets.QLineEdit, "vigshift_key")
        self.vigenere_encode_btn = self.findChild(QPushButton, "vigshift_encode")
        self.vigenere_encode_btn.clicked.connect(lambda: self.do_shift(vigenere_encode, self.vigenere_key_input))
        self.vigenere_decode_btn = self.findChild(QPushButton, "vigshift_decode")
        self.vigenere_decode_btn.clicked.connect(lambda: self.do_shift(vigenere_decode, self.vigenere_key_input))

        self.rsa_keygen_maxprime_input: QSpinBox  = self.findChild(QSpinBox, "rsa_keygen_maxprime_input")
        self.rsa_keygen_maxpq_input: QSpinBox = self.findChild(QSpinBox, "rsa_keygen_maxpq_input")
        self.rsa_keygen_button: QPushButton = self.findChild(QPushButton, "rsa_keygen_button")
        self.rsa_keygen_button.clicked.connect(self.do_rsa_keygen)
        self.rsa_keygen_sharekey_button: QPushButton = self.findChild(QPushButton, "rsa_keygen_sharekey_button")
        self.rsa_keygen_sharekey_button.clicked.connect(self.do_share_key)
        self.rsa_keygen_fillkeys_button: QPushButton = self.findChild(QPushButton, "rsa_keygen_fillkeys_button")
        self.rsa_keygen_fillkeys_button.clicked.connect(self.do_fill_keys)
        self.rsa_keygen_out_pub: QLineEdit = self.findChild(QLineEdit, "rsa_keygen_out_pub")
        self.rsa_keygen_out_priv: QLineEdit = self.findChild(QLineEdit, "rsa_keygen_out_priv")
        self.rsa_encode_pubkey_input: QLineEdit = self.findChild(QLineEdit, "rsa_encode_pubkey_input")
        self.rsa_encode_button: QPushButton = self.findChild(QPushButton, "rsa_encode_button")
        self.rsa_encode_button.clicked.connect(self.do_rsa_encode)
        self.rsa_decode_privkey_input: QLineEdit = self.findChild(QLineEdit, "rsa_decode_privkey_input")
        self.rsa_decode_button: QPushButton = self.findChild(QPushButton, "rsa_decode_button")
        self.rsa_decode_button.clicked.connect(self.do_rsa_decode)

        self.hash_bottom: QLineEdit = self.findChild(QLineEdit, "hash_bottom")
        self.hash_top: QLineEdit = self.findChild(QLineEdit, "hash_top")
        self.hash_hash_button: QPushButton = self.findChild(QPushButton, "hash_hash_button")
        self.hash_hash_button.clicked.connect(self.do_hash)
        self.hash_share_result_button: QPushButton = self.findChild(QPushButton, "hash_share_result_button")
        self.hash_share_result_button.clicked.connect(self.do_share_result)
        self.hash_share_hash_button: QPushButton = self.findChild(QPushButton, "hash_share_hash_button")
        self.hash_share_hash_button.clicked.connect(self.do_share_hash)
        self.hash_verify_button: QPushButton = self.findChild(QPushButton, "hash_verify_button")
        self.hash_verify_button.clicked.connect(self.do_verify_hash)
        self.hash_result_label: QLabel = self.findChild(QLabel, "hash_result_label")

        self.difhel_common_prime: QLineEdit = self.findChild(QLineEdit, "difhel_common_prime")
        self.difhel_generator: QLineEdit = self.findChild(QLineEdit, "difhel_generator")
        self.difhel_our_half_key: QLineEdit = self.findChild(QLineEdit, "difhel_our_half_key")
        self.difhel_our_secret: QLineEdit = self.findChild(QLineEdit, "difhel_our_secret")
        self.difhel_remote_half_key: QLineEdit = self.findChild(QLineEdit, "difhel_remote_half_key")
        self.difhel_shared_secret: QLineEdit = self.findChild(QLineEdit, "difhel_shared_secret")
        self.difhel_maxprime: QSpinBox = self.findChild(QSpinBox, "difhel_maxprime")
        self.difhel_generate_space_button: QPushButton = self.findChild(QPushButton, "difhel_generate_space_button")
        self.difhel_generate_space_button.clicked.connect(self.do_generate_space)
        self.difhel_share_space_button: QPushButton = self.findChild(QPushButton, "difhel_share_space_button")
        self.difhel_share_space_button.clicked.connect(self.do_share_space)
        self.difhel_share_halfkey_button: QPushButton = self.findChild(QPushButton, "difhel_share_half_key_button")
        self.difhel_share_halfkey_button.clicked.connect(self.do_share_halfkey)
        self.difhel_generate_shared_secret_button: QPushButton = self.findChild(QPushButton, "difhel_generate_shared_secret_button")
        self.difhel_generate_shared_secret_button.clicked.connect(self.do_generate_shared_secret)
        self.difhel_share_shared_secret_button: QPushButton = self.findChild(QPushButton, "difhel_share_shared_secret_button")
        self.difhel_share_shared_secret_button.clicked.connect(self.do_share_shared_secret)


        self.server_connect_button: QPushButton = self.findChild(QPushButton, "server_connect_button")
        self.server_connect_button.clicked.connect(self.do_connect)
        self.server_connect_hostname: QLineEdit = self.findChild(QLineEdit, "server_connect_hostname")
        self.server_connect_port: QLineEdit = self.findChild(QLineEdit, "server_connect_port")

        self.radio_server: QtWidgets.QRadioButton = self.findChild(QtWidgets.QRadioButton, "rad_server_message")

    def do_connect(self):
        hostname = self.server_connect_hostname.text()
        port = self.server_connect_port.text()
        self.connect_to_server(hostname, int(port))

    def do_shift(self, lamb, key_source):
        key = None
        if isinstance(key_source, QtWidgets.QLineEdit):
            key = key_source.property("raw") or key_source.text()
        elif isinstance(key_source, QtWidgets.QSpinBox):
            key = key_source.value()

        msg = self.trans_input.property("raw") or str_to_intarray(self.trans_input.toPlainText())
        res = lamb(msg, key)
        self.message_input.setProperty("raw", res)
        print(res)
        self.message_input.setPlainText("".join(["*" for x in res]))

    def do_rsa_keygen(self):
        max_prime = self.rsa_keygen_maxprime_input.value()
        max_pq = self.rsa_keygen_maxpq_input.value()
        (n, e), (_, d) = rsa_keygen(max_prime, max_pq)
        self.rsa_keygen_out_pub.setText(f"({n},{e})")
        self.rsa_keygen_out_priv.setText(f"({n},{d})")

    def do_share_key(self):
        self.message_input.setPlainText(self.rsa_keygen_out_pub.text().strip('(').strip(')'))
        self.message_input.setProperty("raw", None)

    def do_fill_keys(self):
        self.rsa_encode_pubkey_input.setText(self.rsa_keygen_out_pub.text())
        self.rsa_decode_privkey_input.setText(self.rsa_keygen_out_priv.text())

    def do_rsa_encode(self):
        if self.rsa_encode_pubkey_input.text().strip() == "":
            return

        msg = self.trans_input.property("raw")
        (n, e) = self.rsa_encode_pubkey_input.text().strip('(').strip(')').split(",")

        encoded_msg = rsa_encode(msg, e=int(e), n=int(n))

        self.message_input.setPlainText("~" * len(encoded_msg))
        self.message_input.setProperty("raw", encoded_msg)

    def do_rsa_decode(self):
        if self.rsa_decode_privkey_input.text().strip() == "":
            return

        msg = self.trans_input.property("raw")
        (n, d) = self.rsa_decode_privkey_input.text().strip('(').strip(')').split(",")

        decoded_msg = rsa_decode(msg, d=int(d), n=int(n))

        self.message_input.setPlainText("~" * len(decoded_msg))
        self.message_input.setProperty("raw", decoded_msg)

    def do_hash(self):
        msg = self.trans_input.property("raw")
        hash = hash_str(self.trans_input.toPlainText())
        print(hash)
        self.hash_top.setText(binascii.hexlify(hash).decode("ascii"))

    def do_verify_hash(self):
        (top, bottom) = (self.hash_top.text(), self.hash_bottom.text())
        same = top == bottom

        succ_string = self.hash_result_label.property(str(same).lower() + "_string")
        self.hash_result_label.setText(succ_string)

    def do_share_hash(self):
        self.message_input.setPlainText(self.hash_top.text())
        self.message_input.setProperty("raw", None)

    def do_share_result(self):
        self.message_input.setPlainText(str("true" in self.hash_result_label.text()).lower())
        self.message_input.setProperty("raw", None)
        pass

    def do_generate_space(self):
        maxp = self.difhel_maxprime.value()
        p, g, hk, sec = difhel_generate_space(int(maxp))
        self.difhel_common_prime.setText(str(p))
        self.difhel_generator.setText(str(g))
        self.difhel_our_half_key.setText(str(hk))
        self.difhel_our_secret.setText(str(sec))

    def do_share_space(self):
        p, g = self.difhel_common_prime.text(), self.difhel_generator.text()
        self.message_input.setPlainText(f"{p},{g}")

    def do_share_halfkey(self):
        hk = self.difhel_our_half_key.text()
        self.message_input.setPlainText(hk)

    def do_generate_shared_secret(self):
        our_secret = self.difhel_our_secret.text()
        their_halfkey = self.difhel_remote_half_key.text()
        prime = self.difhel_common_prime.text()

        shared_secret = difhel_shared_secret(int(our_secret), int(their_halfkey), int(prime))
        self.difhel_shared_secret.setText(str(shared_secret))
        pass

    def do_share_shared_secret(self):
        shared_secret = self.difhel_shared_secret.text()
        self.message_input.setPlainText(shared_secret)

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent):
        if a0.mimeData().hasUrls():
            a0.acceptProposedAction()

    def dropEvent(self, a0: QtGui.QDropEvent):
        for url in a0.mimeData().urls():
            img = QImage(url.toString(QUrl.UrlFormattingOption.RemoveScheme).lstrip("/"))
            self.send_image_message(img)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.Type.KeyPress and obj is self.message_input:
            if event.key() == QtCore.Qt.Key.Key_Return and self.message_input.hasFocus():
                if event.keyCombination().keyboardModifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
                    return super().eventFilter(obj, event)
                else:
                    self.send_text_message()
                    return True
        return super().eventFilter(obj, event)

    def receive_message(self, message_type: str, message: object, raw: bytearray):
        match message_type:
            case "t" | "s":
                raw_ints = [int.from_bytes(raw[i:i+4], byteorder="big", signed=False) for i in range(0, len(raw), 4)]
                self.display_text_message(message, message_type=message_type, raw_message=raw_ints)
                self.text_messages.append((message, message_type, raw_ints))
            case "i":
                self.display_image_message(message)
            case _:
                raise Exception("Invalid message type received")

    def on_socket_connection_error(self, msg):
        self.display_text_message(f"Connection error: {msg}", color="red", is_system=True)

    def on_socket_connected(self):
        self.display_text_message("Connected!", color="green", is_system=True)

    def display_text_message(self, message, color="#333030", is_system=False, message_type="t", raw_message=None):
        lbl = QtWidgets.QLabel()
        lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse ^ Qt.TextInteractionFlag.TextSelectableByKeyboard)
        lbl.setWordWrap(True)
        if raw_message is not None:
            lbl.mousePressEvent = lambda e: self.transfer_msg(raw_message, message) if e.button() == Qt.MouseButton.MiddleButton else None

        message = message.replace("\n", "<br/>")

        text = strftime("<b>%H:%M</b>", localtime())
        text += f"<font color='{color}'>"
        if is_system:
            text += f" <b>{message}</b>"
        elif message_type == "s":
            text += f" SERVER> <font color=darkgreen>{message}</font>"
        else:
            text += f"~> {message}"
        text += f"</font'>"

        lbl.setText(text)
        self.messages_box.layout().addWidget(lbl)

    def transfer_msg(self, raw: bytearray, msg: str):
            if "n=" in msg and "e=" in msg:
                # RSA task
                n = re.search(r'n=(\d+)', msg).groups()[0]
                e = re.search(r'e=(\d+)', msg).groups()[0]

                self.rsa_encode_pubkey_input.setText(f"({n},{e})")
            elif msg.startswith("You are asked"):
                # Vigenere or shift task
                task_type = self.last_sent_server_message.split(" ")[1]
                key_start_index = msg.rindex(" ") + 1

                val = msg[key_start_index:]
                raw_val = raw[len(raw)-len(val):]
                if task_type == "shift":
                    self.shift_key_input.setValue(int(val))
                elif task_type == "vigenere":
                    self.vigenere_key_input.setText(val)
                    self.vigenere_key_input.setProperty("raw", raw_val)
                elif task_type == "hash":
                    if "verify" in msg:
                        hash_to_check = self.text_messages[-1]
                        self.hash_bottom.setText(str(hash_to_check[0]))
                        self.hash_bottom.setProperty("raw", hash_to_check[2])

                        message_to_hash = self.text_messages[-2]
                        self.trans_input.setPlainText(message_to_hash[0])
                        self.trans_input.setProperty("raw", message_to_hash[2])
                        pass
                    else:
                        message_to_hash = self.text_messages[-1]
                        self.trans_input.setPlainText(message_to_hash[0])
                        self.trans_input.setProperty("raw", message_to_hash[2])
                        pass
            else:
                self.trans_input.setPlainText(msg)
                self.trans_input.setProperty("raw", raw)
                print(raw)

    def display_image_message(self, image):
        pixmap = QPixmap.fromImage(image)

        time_lbl = QtWidgets.QLabel()
        time_lbl.setText(strftime("<b>%H:%M</b>", localtime()))
        self.messages_box.layout().addWidget(time_lbl)

        img_lbl = QtWidgets.QLabel()
        img_lbl.setPixmap(pixmap.scaled(64*3, 64*3, Qt.AspectRatioMode.KeepAspectRatio))
        self.messages_box.layout().addWidget(img_lbl)

    def send_text_message(self):
        msg_type = "s" if self.radio_server.isChecked() else "t"

        if self.message_input.property("raw") is not None:
            message_data = build_text_message_intarray(self.message_input.property("raw"), msg_type)
        else:
            msg: str = self.message_input.toPlainText()

            if len(msg.strip()) == 0:  # Don't send only whitespace
                return

            message_data = build_text_message(msg, msg_type)

            if msg_type == "s":
                # store the last sent server message
                self.last_sent_server_message = msg

        self.message_sent.emit(message_data)
        self.message_input.clear()  # Clear line input
        self.message_input.setProperty("raw", None)

    def send_image_message(self, img: QImage):
        if not img:
            return

        if img.width() > 128 or img.height() > 128:
            QMessageBox.warning(self, "", "Selected image is too big.\nMaximum size: 128x128 pixels.")
            return

        message_data = build_image_message(img)
        self.message_sent.emit(message_data)

    def open_image_picker(self):
        file_name = QFileDialog.getOpenFileName(self, "Open image", "/", "Image Files (*.png *.jpg *.jpeg *.pbm *pgm *xbm *xpm *.bmp)")
        self.send_image_message(QImage(file_name[0]))

    def update_scroll(self):
        if self.scroll_follow_new:
            self.vertical_scroll_bar.setValue(self.vertical_scroll_bar.maximum())

    def update_scroll_follow_new(self):
        self.scroll_follow_new = self.vertical_scroll_bar.value() == self.vertical_scroll_bar.maximum()
