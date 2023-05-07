from typing import List

def get_primes(n: int) -> List[int]:
    sieve = [False] * n
    for i in range(2, n):
        if not sieve[i]:
            for j in range(i + i, n, i):
                sieve[j] = True
    return [num for (num, marked) in enumerate(sieve) if not marked][2:]

def gcd(a: int, b: int) -> int:
    if b == 0:
        return a
    else:
        return gcd(b, a % b)

def extended_euclid(a: int, b: int) -> (int, int, int):
    if b == 0:
        return a, 1, 0
    else:
        (d, x, y) = extended_euclid(b, a % b)
        return d, y, x - (a // b) * y

def power_modulo(base: int, exponent: int, mod: int) -> int:
    curr_exponent = 2
    curr_power = base
    power_list = [base]
    while curr_exponent < exponent:
        curr_power = (curr_power * curr_power) % mod
        power_list.append(curr_power)
        curr_exponent *= 2
    result = 1
    remaining_exponent = exponent
    for i in range(len(power_list) - 1, -1, -1):
        if remaining_exponent - (2 ** i) >= 0:
            remaining_exponent -= 2 ** i
            result = (result * power_list[i]) % mod
    return result

def is_primitive_root(m: int, root: int) -> bool:
    if not is_prime(m):
        return False
    factors = prime_factors(m - 1)
    return all(power_modulo(root, (m - 1) // p, m) != 1 for p in factors)

def find_primitive_root(m: int) -> int:
    if not is_prime(m):
        return None
    primes = get_primes(m)
    for i in range(2, len(primes)):
        candidate = primes[i]
        if is_primitive_root(m, candidate):
            return candidate
    return None

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def prime_factors(n: int) -> set:
    factors = []
    i = 2
    while i * i <= n:
        if n % i:
            i += 1
        else:
            n //= i
            factors.append(i)
    if n > 1:
        factors.append(n)
    return set(factors)
