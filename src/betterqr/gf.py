"""
Galois Field GF(2^8) arithmetic for Reed-Solomon error correction.
Primitive polynomial: x^8 + x^4 + x^3 + x^2 + 1  (0x11D)
"""

# Build log and anti-log (exp) tables
_EXP = [0] * 512
_LOG = [0] * 256

_val = 1
for _i in range(255):
    _EXP[_i] = _val
    _LOG[_val] = _i
    _val <<= 1
    if _val & 0x100:
        _val ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return _EXP[_LOG[a] + _LOG[b]]


def gf_pow(a: int, n: int) -> int:
    return _EXP[(_LOG[a] * n) % 255]


def gf_div(a: int, b: int) -> int:
    if b == 0:
        raise ZeroDivisionError("GF division by zero")
    if a == 0:
        return 0
    return _EXP[(_LOG[a] - _LOG[b]) % 255]


def gf_poly_mul(p: list, q: list) -> list:
    """Multiply two polynomials in GF(256)."""
    result = [0] * (len(p) + len(q) - 1)
    for j, qv in enumerate(q):
        for i, pv in enumerate(p):
            result[i + j] ^= gf_mul(pv, qv)
    return result


def gf_poly_div(dividend: list, divisor: list) -> list:
    """Divide dividend polynomial by divisor, return remainder."""
    msg = list(dividend)
    for i in range(len(dividend) - len(divisor) + 1):
        coef = msg[i]
        if coef != 0:
            for j in range(1, len(divisor)):
                if divisor[j] != 0:
                    msg[i + j] ^= gf_mul(divisor[j], coef)
    return msg[-(len(divisor) - 1):]


def generator_polynomial(n_ec_codewords: int) -> list:
    """Build the generator polynomial for n EC codewords."""
    g = [1]
    for i in range(n_ec_codewords):
        g = gf_poly_mul(g, [1, gf_pow(2, i)])
    return g


def rs_encode(data: list, n_ec_codewords: int) -> list:
    """Return the EC codewords for data using Reed-Solomon."""
    gen = generator_polynomial(n_ec_codewords)
    # Pad data with zeros to make room for EC
    padded = list(data) + [0] * n_ec_codewords
    remainder = gf_poly_div(padded, gen)
    return remainder
