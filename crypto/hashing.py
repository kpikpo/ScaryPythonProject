import hashlib


def hash_int_array(a: list[int]) -> bytes:
    sha = hashlib.sha256()
    sha.update(bytes(a))
    return sha.digest()


def hash_str(s: str) -> bytes:
    sha = hashlib.sha256()
    sha.update(s.encode())
    return sha.digest()
