from typing import List

from PyQt6.QtGui import QImage


def get_common_header() -> bytearray:
    return bytearray(b"ISC")


def str_to_intarray(input: str) -> List[int]:
    return [int.from_bytes(bytes(c, "utf-8"), "big") for c in input]


def intarray_to_str(input: List[int]) -> str:
    return ""


def build_text_message(text: str, type:str = "t") -> bytearray:
    return build_text_message_intarray(str_to_intarray(text), type)


def build_text_message_intarray(content: List[int], type: str = "t") -> bytearray:
    if len(content) > 0xffff:
        raise Exception("Message text shouldn't exceed 65'535 characters")

    data = get_common_header()
    data.append(ord(type))

    # Add text length
    data.extend(len(content).to_bytes(2, "big"))

    # Add characters
    for char in content:
        data.extend(char.to_bytes(4, "big"))

    return data


def build_image_message(image_data: QImage) -> bytearray:
    if image_data.width() > 128 or image_data.height() > 128:
        raise Exception("Image exceeds maximum resolution (128x128 pixels)")

    data = get_common_header()
    data.append(ord(b"i"))

    data.append(image_data.width())
    data.append(image_data.height())
    print(f"Building message for image of dim: {image_data.width()}x{image_data.height()}")

    for x in range(0, image_data.width()):
        for y in range(0, image_data.height()):
            rgb = image_data.pixelColor(x, y)
            data.extend([rgb.red(), rgb.green(), rgb.blue()])

    print(f"Pixel data bytes: {len(data[6:])}")
    return data
