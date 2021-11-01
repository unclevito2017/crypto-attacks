import logging
from math import gcd
from math import lcm

from sage.all import crt
from sage.all import is_prime
from sage.all import kronecker
from sage.all import next_prime


def _generate_s(A, k):
    S = []
    for a in A:
        # Possible non-residues mod 4a of potential primes p
        Sa = set()
        for p in range(1, 4 * a, 2):
            if kronecker(a, p) == -1:
                Sa.add(p)

        # Subsets of Sa that meet the intersection requirement
        Sk = []
        for ki in k:
            assert gcd(ki, 4 * a) == 1
            Sk.append({pow(ki, -1, 4 * a) * (s + ki - 1) % (4 * a) for s in Sa})

        S.append(Sa.intersection(*Sk))

    return S


# Brute forces a combination of residues from S by backtracking
# rems already contains the remainders mod each k
# mods already contains each k
def _backtrack(S, A, rems, mods, i):
    if i == len(S):
        return crt(rems, mods), lcm(*mods)

    mods.append(4 * A[i])
    for za in S[i]:
        rems.append(za)
        try:
            crt(rems, mods)
            z, m = _backtrack(S, A, rems, mods, i + 1)
            if z is not None and m is not None:
                return z, m
        except ValueError:
            pass
        rems.pop()

    mods.pop()
    return None, None


def generate_pseudoprime(A, min_bitsize=0):
    """
    Generates a pseudoprime of the form p1 * p2 * p3 which passes the Miller-Rabin primality test for the provided bases.
    More information: R. Albrecht M. et al., "Prime and Prejudice: Primality Testing Under Adversarial Conditions"
    :param A: the bases
    :param min_bitsize: the minimum bitsize of the generated pseudoprime (default: 0)
    :return: a tuple containing the pseudoprime n, as well as its 3 prime factors
    """
    A.sort()
    k2 = int(next_prime(A[-1]))
    k3 = int(next_prime(k2))
    while True:
        logging.info(f"Trying k2 = {k2} and k3 = {k3}...")
        rems = [pow(-k3, -1, k2), pow(-k2, -1, k3)]
        mods = [k2, k3]
        s = _generate_s(A, mods)
        z, m = _backtrack(s, A, rems, mods, 0)
        if z and m:
            logging.info(f"Found residue {z} and modulus {m}")
            i = (2 ** (min_bitsize // 3)) // m
            while True:
                p1 = int(z + i * m)
                p2 = k2 * (p1 - 1) + 1
                p3 = k3 * (p1 - 1) + 1
                if is_prime(p1) and is_prime(p2) and is_prime(p3):
                    return p1 * p2 * p3, p1, p2, p3

                i += 1
        else:
            k3 = int(next_prime(k3))
