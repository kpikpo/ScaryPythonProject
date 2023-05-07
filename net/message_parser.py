from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QImage, QColor


class MessageParser:
    def __init__(self):
        self.message_type = None
        self.content_bytes_left = None
        self.content_bytes = bytearray()
        self.gulps = 0
        self.messages = []

    def clear(self):
        self.message_type = None
        self.content_bytes_left = -1
        self.content_bytes = bytearray()
        self.gulps = 0

    def add_bytes(self, msgbytes: bytearray):
        if len(msgbytes) == 0:
            return
        if self.message_type is None:
            msgbytes = self.parse_header(msgbytes)

        to_read = min(len(msgbytes), self.content_bytes_left)
        self.content_bytes.extend(msgbytes)
        self.content_bytes_left -= to_read
        self.gulps += 1

        if self.is_current_message_complete():
            # We've finished reading the bytes for the current message

            self.messages.append(self.parse_message())
            self.clear()

            if len(msgbytes[to_read:]) != 0:
                # ... but we have bytes left to read for another message
                self.add_bytes(msgbytes[to_read:])

    def parse_header(self, msgbytes: bytearray) -> bytearray:
        if msgbytes[0:3] != b"ISC":
            raise Exception(f"Message header invalid: Received {msgbytes[0:3]}")

        self.message_type = chr(msgbytes[3])
        match chr(msgbytes[3]):
            case "t" | "s":
                self.content_bytes_left = int.from_bytes(msgbytes[4:6], "big") * 4
                self.content_bytes.extend(msgbytes[4:6])
                return msgbytes[6:]
            case "i":
                self.content_bytes_left = msgbytes[4] * msgbytes[5] * 3
                self.content_bytes.extend(msgbytes[4:6])
                return msgbytes[6:]
            case _:
                raise Exception(f"Message type unknown: Received {chr(msgbytes[3])}")

    def parse_message(self) -> (str, object, object):
        if not self.is_current_message_complete():
            return None

        if self.message_type == "t" or self.message_type == "s":
            return self.message_type, parse_text_message(self.content_bytes), self.content_bytes[2:]
        elif self.message_type == "i":
            return self.message_type, parse_image_message(self.content_bytes), self.content_bytes[2:]

    def is_current_message_complete(self) -> bool:
        return self.content_bytes_left == 0

    def consume_messages(self) -> [(str, object)]:
        msgs = self.messages
        self.messages = []
        return msgs


def parse_text_message(message_data: bytearray) -> str:
    char_count = int.from_bytes(message_data[0:2], "big")
    text = message_data[2:]
    out = ""
    for c in range(char_count):
        try:
            de = text[c*4:c*4 + 4].decode("utf-8").lstrip("\x00")
            out += de if de.isprintable() else "�"
        except:
            pass # todo: handle this better maybe

    return out


def parse_image_message(message_data: bytearray) -> QImage:
    width = message_data[0]
    height = message_data[1]
    print(f"parsing image with dim {width}x{height}")
    color_data = message_data[2:]
    print(f"Number of bytes for pixel data: {len(color_data)}")

    if len(color_data) != width*height*3:
        raise Exception(f"Bad image! Message data - {width}x{height} should have {width*height*3} bytes,"
                        f" received {len(color_data)}:\n\n{message_data}\n\n")

    out = QImage(width, height, QImage.Format.Format_RGB32)
    for pixel in range(width * height):
        (r, g, b) = (color_data[pixel * 3], color_data[pixel * 3 + 1], color_data[pixel * 3 + 2])
        out.setPixelColor(QPoint(pixel // height, pixel % height), QColor(r, g, b))

    return out
