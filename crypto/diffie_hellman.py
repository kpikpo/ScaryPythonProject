from mathematics.math_utils import get_primes, power_modulo, find_primitive_root
from mathematics.rand import Rand


def difhel_generate_space(max_prime):
    prime_numbers = get_primes(max_prime)
    rng = Rand()

    # Pick a random prime number
    prime = prime_numbers[rng.next_int_in_range(max=len(prime_numbers))]

    # Generate a random secret number
    secret_number = rng.next_int_in_range(max=1000)

    # Find the primitive root of prime
    pm = find_primitive_root(prime)

    # Compute half-key
    half_key = power_modulo(pm, secret_number, prime)

    return prime, pm, half_key, secret_number


def difhel_shared_secret(local_secret, remote_halfkey, prime):
    return power_modulo(remote_halfkey, local_secret, prime)


if __name__ == "__main__":
    prime, pm, half_key, secret_number = difhel_generate_space(5000)
    print("Prime: ", prime)
    print("Primitive root of prime: ", pm)
    print("Half-key: ", half_key)
    print("Secret number: ", secret_number)
