import array
from typing import Callable

def vigenere_encode(message: array.array, key: str) -> array.array:
    # convert string key to array of integer ASCII values
    if isinstance(key, str):
        key = array.array('i', (ord(c) for c in key))

    # encode message using Vigenere cipher
    return shift(message, key, lambda a, b: a+b)


def vigenere_decode(message: array.array, key: str | array.array) -> array.array:
    # convert string key to array of integer ASCII values
    if isinstance(key, str):
        key = array.array('i', (ord(c) for c in key))

    # decode message using Vigenere cipher
    return shift(message, key, lambda a, b: a-b)


def numerical_encode(message: array.array, key: int) -> array.array:
    # encode message using numerical shift cipher
    return shift(message, array.array('i', (key,)), lambda a, b: a+b)


def numerical_decode(message: array.array, key: int) -> array.array:
    # decode message using numerical shift cipher
    return shift(message, array.array('i', (key,)), lambda a, b: a-b)


def shift(message: array.array, key: array.array, operation: Callable[[int, int], int]) -> array.array:
    # initialize index for iterating through key
    key_index = 0

    # initialize empty array for output message
    output_message = array.array('i')

    # iterate through each character in message
    for character in message:
        # apply shift operation to character and corresponding key value
        shifted_value = operation(character, key[key_index])

        # append shifted value to output message
        output_message.append(shifted_value)

        # update key index for next character in message
        key_index = (key_index + 1) % len(key)

    # return output message as array
    return output_message
