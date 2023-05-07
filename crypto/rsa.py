import time

from mathematics.math_utils import *
from mathematics.rand import Rand

MAX_PRIME = 256**2 * 128
MAX_PQ = 256**4


def rsa_keygen(max_prime=MAX_PRIME, max_pq=MAX_PQ):
    rng = Rand()

    # Generate prime numbers up to MAX_PRIME
    prime_numbers = get_primes(max_prime)

    # Pick a random p
    p = prime_numbers.pop(rng.next_int_in_range(max=len(prime_numbers) - 1))

    # Pick a random q so that p*q < MAX_PQ
    biggest_q_index = next((idx for (idx, v) in enumerate(prime_numbers) if v > max_pq / p),
                           len(prime_numbers) - 2)
    q = prime_numbers.pop(rng.next_int_in_range(max=biggest_q_index))

    # Compute n and k
    n = p * q
    k = (p - 1) * (q - 1)

    # Pick random e < k coprime with k
    i = next((idx for (idx, v) in enumerate(prime_numbers) if v > k), len(prime_numbers))
    e_bag = prime_numbers[:i]
    e = None
    while len(e_bag) > 0:
        e = e_bag.pop()
        if gcd(e, k) == 1:
            break

    # Compute d and ensure b is negative
    _, d, b = extended_euclid(e, k)
    dd, bb = d + k, b - e

    return (n, e), (n, dd)


def rsa_encode(a: List[int], e: int, n: int) -> List[int]:
    return rsa_transform(a, e, n)


def rsa_decode(k: List[int], d: int, n: int) -> List[int]:
    return rsa_transform(k, d, n)


def rsa_transform(nums: List[int], exponent: int, mod_space: int) -> List[int]:
    out = []
    for num in nums:
        out.append(power_modulo(num, exponent, mod_space))

    return out


if __name__ == '__main__':
    (n, e), (_, d) = rsa_keygen(256**2, 256**3)

    t = time.time()
    ints = [114, 105, 110, 99, 105, 112, 97, 108, 101, 109, 101, 110, 116, 32, 100, 97, 110, 115, 32, 108, 101, 115, 32, 109, 105]
    print("Encoding: ", ints)
    print("with keys", n, e)

    enc = rsa_encode(ints, e, n)
    print("encoded: ", enc)

    dec = rsa_decode(enc, d, n)
    print("decoded: ", dec)
    print("with keys", d, n)

    print(f"Took {time.time() - t} secs")
