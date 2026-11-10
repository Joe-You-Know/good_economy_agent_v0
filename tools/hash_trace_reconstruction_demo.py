"""Safe local hash trace-reconstruction demo.

This does not observe browsers, wallets, OS processes, or external systems.
It instruments its own SHA-256 and RIPEMD-160 single-block computations,
records one forward internal-state trace, and reconstructs the original padded
message block from that trace without recording message words.

The narrow claim tested here:
  If a single execution trace exposes sufficiently rich internal round state,
  SHA-256 and RIPEMD-160 message blocks are algebraically recoverable.

The capture layer is intentionally out of scope. This is not spyware.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable


MASK = 0xFFFFFFFF
MESSAGE = b"good-economy single-trace hash test"


def u32(x: int) -> int:
    return x & MASK


def rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & MASK


def rotl(x: int, n: int) -> int:
    return ((x << n) | (x >> (32 - n))) & MASK


def ror(x: int, n: int) -> int:
    return rotr(x, n)


def sha256_pad_one_block(message: bytes) -> bytes:
    if len(message) >= 56:
        raise ValueError("demo uses one SHA-256 block")
    bit_len = len(message) * 8
    return message + b"\x80" + b"\x00" * (55 - len(message)) + bit_len.to_bytes(8, "big")


def ripemd160_pad_one_block(message: bytes) -> bytes:
    if len(message) >= 56:
        raise ValueError("demo uses one RIPEMD-160 block")
    bit_len = len(message) * 8
    return message + b"\x80" + b"\x00" * (55 - len(message)) + bit_len.to_bytes(8, "little")


def unpad_single_block(block: bytes, endian: str) -> bytes:
    idx = block.find(b"\x80")
    if idx < 0:
        raise ValueError("padding marker not found")
    msg = block[:idx]
    pad_zeros = block[idx + 1 : 56]
    if any(pad_zeros):
        raise ValueError("nonzero padding bytes")
    bit_len = int.from_bytes(block[56:64], endian)
    if bit_len != len(msg) * 8:
        raise ValueError("length field mismatch")
    return msg


SHA256_H0 = (
    0x6A09E667,
    0xBB67AE85,
    0x3C6EF372,
    0xA54FF53A,
    0x510E527F,
    0x9B05688C,
    0x1F83D9AB,
    0x5BE0CD19,
)

SHA256_K = (
    0x428A2F98,
    0x71374491,
    0xB5C0FBCF,
    0xE9B5DBA5,
    0x3956C25B,
    0x59F111F1,
    0x923F82A4,
    0xAB1C5ED5,
    0xD807AA98,
    0x12835B01,
    0x243185BE,
    0x550C7DC3,
    0x72BE5D74,
    0x80DEB1FE,
    0x9BDC06A7,
    0xC19BF174,
    0xE49B69C1,
    0xEFBE4786,
    0x0FC19DC6,
    0x240CA1CC,
    0x2DE92C6F,
    0x4A7484AA,
    0x5CB0A9DC,
    0x76F988DA,
    0x983E5152,
    0xA831C66D,
    0xB00327C8,
    0xBF597FC7,
    0xC6E00BF3,
    0xD5A79147,
    0x06CA6351,
    0x14292967,
    0x27B70A85,
    0x2E1B2138,
    0x4D2C6DFC,
    0x53380D13,
    0x650A7354,
    0x766A0ABB,
    0x81C2C92E,
    0x92722C85,
    0xA2BFE8A1,
    0xA81A664B,
    0xC24B8B70,
    0xC76C51A3,
    0xD192E819,
    0xD6990624,
    0xF40E3585,
    0x106AA070,
    0x19A4C116,
    0x1E376C08,
    0x2748774C,
    0x34B0BCB5,
    0x391C0CB3,
    0x4ED8AA4A,
    0x5B9CCA4F,
    0x682E6FF3,
    0x748F82EE,
    0x78A5636F,
    0x84C87814,
    0x8CC70208,
    0x90BEFFFA,
    0xA4506CEB,
    0xBEF9A3F7,
    0xC67178F2,
)


def sha_ch(x: int, y: int, z: int) -> int:
    return (x & y) ^ (~x & z)


def sha_maj(x: int, y: int, z: int) -> int:
    return (x & y) ^ (x & z) ^ (y & z)


def sha_big0(x: int) -> int:
    return rotr(x, 2) ^ rotr(x, 13) ^ rotr(x, 22)


def sha_big1(x: int) -> int:
    return rotr(x, 6) ^ rotr(x, 11) ^ rotr(x, 25)


def sha_small0(x: int) -> int:
    return rotr(x, 7) ^ rotr(x, 18) ^ (x >> 3)


def sha_small1(x: int) -> int:
    return rotr(x, 17) ^ rotr(x, 19) ^ (x >> 10)


@dataclass(frozen=True)
class Sha256Trace:
    initial_state: tuple[int, ...]
    round_states: tuple[tuple[int, ...], ...]
    final_state: tuple[int, ...]


def sha256_trace(message: bytes) -> tuple[Sha256Trace, bytes]:
    block = sha256_pad_one_block(message)
    words = [int.from_bytes(block[i : i + 4], "big") for i in range(0, 64, 4)]
    for i in range(16, 64):
        words.append(u32(sha_small1(words[i - 2]) + words[i - 7] + sha_small0(words[i - 15]) + words[i - 16]))

    a, b, c, d, e, f, g, h = SHA256_H0
    states: list[tuple[int, ...]] = []
    for i in range(64):
        t1 = u32(h + sha_big1(e) + sha_ch(e, f, g) + SHA256_K[i] + words[i])
        t2 = u32(sha_big0(a) + sha_maj(a, b, c))
        h = g
        g = f
        f = e
        e = u32(d + t1)
        d = c
        c = b
        b = a
        a = u32(t1 + t2)
        states.append((a, b, c, d, e, f, g, h))

    final_state = tuple(u32(x + y) for x, y in zip(SHA256_H0, (a, b, c, d, e, f, g, h)))
    return Sha256Trace(SHA256_H0, tuple(states), final_state), block


def sha256_reconstruct_block(trace: Sha256Trace) -> bytes:
    recovered_w: list[int] = []
    prev = trace.initial_state
    for i, post in enumerate(trace.round_states):
        a, b, c, d, e, f, g, h = prev
        post_e = post[4]
        t1 = u32(post_e - d)
        recovered_w.append(u32(t1 - h - sha_big1(e) - sha_ch(e, f, g) - SHA256_K[i]))
        prev = post

    # Verify extension consistency, then recover the original 16 words.
    for i in range(16, 64):
        expected = u32(sha_small1(recovered_w[i - 2]) + recovered_w[i - 7] + sha_small0(recovered_w[i - 15]) + recovered_w[i - 16])
        if recovered_w[i] != expected:
            raise ValueError(f"SHA-256 schedule mismatch at W[{i}]")
    return b"".join(w.to_bytes(4, "big") for w in recovered_w[:16])


RIPEMD_H0 = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0)

RIPEMD_R1 = (
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
    3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
    1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
    4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13,
)
RIPEMD_R2 = (
    5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
    6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
    15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
    8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
    12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11,
)
RIPEMD_S1 = (
    11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
    7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
    11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
    11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
    9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6,
)
RIPEMD_S2 = (
    8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
    9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
    9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
    15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
    8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11,
)


def ripemd_f(j: int, x: int, y: int, z: int) -> int:
    if j <= 15:
        return x ^ y ^ z
    if j <= 31:
        return (x & y) | (~x & z)
    if j <= 47:
        return (x | ~y) ^ z
    if j <= 63:
        return (x & z) | (y & ~z)
    return x ^ (y | ~z)


def ripemd_k1(j: int) -> int:
    return (0x00000000, 0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xA953FD4E)[j // 16]


def ripemd_k2(j: int) -> int:
    return (0x50A28BE6, 0x5C4DD124, 0x6D703EF3, 0x7A6D76E9, 0x00000000)[j // 16]


def ripemd_f2(j: int, x: int, y: int, z: int) -> int:
    return ripemd_f(79 - j, x, y, z)


@dataclass(frozen=True)
class Ripemd160Trace:
    initial_state: tuple[int, ...]
    left_states: tuple[tuple[int, ...], ...]
    right_states: tuple[tuple[int, ...], ...]
    final_state: tuple[int, ...]


def ripemd160_trace(message: bytes) -> tuple[Ripemd160Trace, bytes]:
    block = ripemd160_pad_one_block(message)
    words = [int.from_bytes(block[i : i + 4], "little") for i in range(0, 64, 4)]

    al, bl, cl, dl, el = RIPEMD_H0
    ar, br, cr, dr, er = RIPEMD_H0
    left_states: list[tuple[int, ...]] = []
    right_states: list[tuple[int, ...]] = []

    for j in range(80):
        t = u32(rotl(u32(al + ripemd_f(j, bl, cl, dl) + words[RIPEMD_R1[j]] + ripemd_k1(j)), RIPEMD_S1[j]) + el)
        al, el, dl, cl, bl = el, dl, rotl(cl, 10), bl, t
        left_states.append((al, bl, cl, dl, el))

        t = u32(rotl(u32(ar + ripemd_f2(j, br, cr, dr) + words[RIPEMD_R2[j]] + ripemd_k2(j)), RIPEMD_S2[j]) + er)
        ar, er, dr, cr, br = er, dr, rotl(cr, 10), br, t
        right_states.append((ar, br, cr, dr, er))

    h0, h1, h2, h3, h4 = RIPEMD_H0
    t = u32(h1 + cl + dr)
    h1 = u32(h2 + dl + er)
    h2 = u32(h3 + el + ar)
    h3 = u32(h4 + al + br)
    h4 = u32(h0 + bl + cr)
    h0 = t
    final_state = (h0, h1, h2, h3, h4)
    return Ripemd160Trace(RIPEMD_H0, tuple(left_states), tuple(right_states), final_state), block


def ripemd_recover_word(
    pre: tuple[int, ...],
    post: tuple[int, ...],
    rotate: int,
    k_value: int,
    f_func: Callable[[int, int, int], int],
) -> int:
    a, b, c, d, e = pre
    post_b = post[1]
    before_rot = ror(u32(post_b - e), rotate)
    return u32(before_rot - a - f_func(b, c, d) - k_value)


def ripemd160_reconstruct_block(trace: Ripemd160Trace) -> bytes:
    candidates: dict[int, list[int]] = {i: [] for i in range(16)}
    prev_left = trace.initial_state
    prev_right = trace.initial_state
    for j in range(80):
        post_left = trace.left_states[j]
        word_left = ripemd_recover_word(
            prev_left,
            post_left,
            RIPEMD_S1[j],
            ripemd_k1(j),
            lambda b, c, d, jj=j: ripemd_f(jj, b, c, d),
        )
        candidates[RIPEMD_R1[j]].append(word_left)
        prev_left = post_left

        post_right = trace.right_states[j]
        word_right = ripemd_recover_word(
            prev_right,
            post_right,
            RIPEMD_S2[j],
            ripemd_k2(j),
            lambda b, c, d, jj=j: ripemd_f2(jj, b, c, d),
        )
        candidates[RIPEMD_R2[j]].append(word_right)
        prev_right = post_right

    words: list[int] = []
    for i in range(16):
        uniq = sorted(set(candidates[i]))
        if len(uniq) != 1:
            raise ValueError(f"RIPEMD-160 word {i} inconsistent: {uniq[:5]}")
        words.append(uniq[0])
    return b"".join(w.to_bytes(4, "little") for w in words)


def digest_hex_from_state(state: tuple[int, ...], endian: str) -> str:
    return b"".join(x.to_bytes(4, endian) for x in state).hex()


def main() -> None:
    sha_trace_obj, sha_block = sha256_trace(MESSAGE)
    sha_recovered_block = sha256_reconstruct_block(sha_trace_obj)
    sha_recovered_message = unpad_single_block(sha_recovered_block, "big")
    sha_digest = digest_hex_from_state(sha_trace_obj.final_state, "big")

    ripemd_trace_obj, ripemd_block = ripemd160_trace(MESSAGE)
    ripemd_recovered_block = ripemd160_reconstruct_block(ripemd_trace_obj)
    ripemd_recovered_message = unpad_single_block(ripemd_recovered_block, "little")
    ripemd_digest = digest_hex_from_state(ripemd_trace_obj.final_state, "little")

    result = {
        "demo": "single_forward_hash_trace_reconstruction",
        "scope": "instrumented_local_single_block_hashes_only",
        "message": MESSAGE.decode("ascii"),
        "records_message_words": False,
        "records_input_bytes": False,
        "records_operation_labels": False,
        "sha256": {
            "round_state_trace_blocks": len(sha_trace_obj.round_states),
            "recovered_block_match": sha_recovered_block == sha_block,
            "recovered_message": sha_recovered_message.decode("ascii"),
            "recovered_message_match": sha_recovered_message == MESSAGE,
            "digest": sha_digest,
            "hashlib_digest_match": sha_digest == hashlib.sha256(MESSAGE).hexdigest(),
        },
        "ripemd160": {
            "left_trace_blocks": len(ripemd_trace_obj.left_states),
            "right_trace_blocks": len(ripemd_trace_obj.right_states),
            "recovered_block_match": ripemd_recovered_block == ripemd_block,
            "recovered_message": ripemd_recovered_message.decode("ascii"),
            "recovered_message_match": ripemd_recovered_message == MESSAGE,
            "digest": ripemd_digest,
            "hashlib_digest_match": ripemd_digest == hashlib.new("ripemd160", MESSAGE).hexdigest(),
        },
        "claim_validated": (
            "If a single forward trace exposes sufficiently rich internal "
            "round/register state, SHA-256 and RIPEMD-160 message blocks are "
            "algebraically recoverable in this controlled setting."
        ),
        "not_validated": [
            "passive browser tracing",
            "EM/power/cache capture fidelity",
            "raw NAND-packet segmentation from physical traces",
            "multi-block streaming recovery",
            "secret recovery from public digest alone",
            "third-party system observation",
        ],
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
