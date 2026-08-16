"""Small, dependency-free BLAKE3 reference implementation for TCPS receipts.

This module implements the unkeyed 32-byte hash mode used by TCPS. It is
intentionally scalar and optimized for auditability rather than throughput.
"""
from __future__ import annotations

from dataclasses import dataclass

IV = (
    0x6A09E667,
    0xBB67AE85,
    0x3C6EF372,
    0xA54FF53A,
    0x510E527F,
    0x9B05688C,
    0x1F83D9AB,
    0x5BE0CD19,
)
MSG_PERMUTATION = (2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8)
CHUNK_START = 1
CHUNK_END = 2
PARENT = 4
ROOT = 8
BLOCK_LEN = 64
CHUNK_LEN = 1024
MASK32 = 0xFFFFFFFF


def _rotr32(value: int, count: int) -> int:
    return ((value >> count) | (value << (32 - count))) & MASK32


def _g(state: list[int], a: int, b: int, c: int, d: int, mx: int, my: int) -> None:
    state[a] = (state[a] + state[b] + mx) & MASK32
    state[d] = _rotr32(state[d] ^ state[a], 16)
    state[c] = (state[c] + state[d]) & MASK32
    state[b] = _rotr32(state[b] ^ state[c], 12)
    state[a] = (state[a] + state[b] + my) & MASK32
    state[d] = _rotr32(state[d] ^ state[a], 8)
    state[c] = (state[c] + state[d]) & MASK32
    state[b] = _rotr32(state[b] ^ state[c], 7)


def _round(state: list[int], message: list[int]) -> None:
    _g(state, 0, 4, 8, 12, message[0], message[1])
    _g(state, 1, 5, 9, 13, message[2], message[3])
    _g(state, 2, 6, 10, 14, message[4], message[5])
    _g(state, 3, 7, 11, 15, message[6], message[7])
    _g(state, 0, 5, 10, 15, message[8], message[9])
    _g(state, 1, 6, 11, 12, message[10], message[11])
    _g(state, 2, 7, 8, 13, message[12], message[13])
    _g(state, 3, 4, 9, 14, message[14], message[15])


def _permute(message: list[int]) -> list[int]:
    return [message[index] for index in MSG_PERMUTATION]


def _words(block: bytes) -> list[int]:
    padded = block + b"\x00" * (BLOCK_LEN - len(block))
    return [int.from_bytes(padded[i : i + 4], "little") for i in range(0, BLOCK_LEN, 4)]


def _compress(
    chaining_value: tuple[int, ...] | list[int],
    block_words: list[int],
    counter: int,
    block_len: int,
    flags: int,
) -> list[int]:
    cv = list(chaining_value)
    state = cv + list(IV[:4]) + [counter & MASK32, (counter >> 32) & MASK32, block_len, flags]
    message = list(block_words)
    for _ in range(7):
        _round(state, message)
        message = _permute(message)
    for i in range(8):
        state[i] ^= state[i + 8]
        state[i + 8] ^= cv[i]
    return [word & MASK32 for word in state]


def _serialize_words(words: list[int]) -> bytes:
    return b"".join(word.to_bytes(4, "little") for word in words)


@dataclass(frozen=True)
class _Output:
    input_cv: tuple[int, ...]
    block_words: tuple[int, ...]
    counter: int
    block_len: int
    flags: int

    def chaining_value(self) -> tuple[int, ...]:
        return tuple(
            _compress(self.input_cv, list(self.block_words), self.counter, self.block_len, self.flags)[:8]
        )

    def root_bytes(self, length: int) -> bytes:
        result = bytearray()
        output_block_counter = 0
        while len(result) < length:
            words = _compress(
                self.input_cv,
                list(self.block_words),
                output_block_counter,
                self.block_len,
                self.flags | ROOT,
            )
            result.extend(_serialize_words(words))
            output_block_counter += 1
        return bytes(result[:length])


def _chunk_output(chunk: bytes, chunk_counter: int) -> _Output:
    if len(chunk) > CHUNK_LEN:
        raise ValueError("chunk exceeds BLAKE3 chunk length")
    block_count = max(1, (len(chunk) + BLOCK_LEN - 1) // BLOCK_LEN)
    cv: tuple[int, ...] = IV
    for block_index in range(block_count):
        block = chunk[block_index * BLOCK_LEN : (block_index + 1) * BLOCK_LEN]
        flags = 0
        if block_index == 0:
            flags |= CHUNK_START
        if block_index == block_count - 1:
            flags |= CHUNK_END
        output = _Output(cv, tuple(_words(block)), chunk_counter, len(block), flags)
        if block_index == block_count - 1:
            return output
        cv = output.chaining_value()
    raise AssertionError("unreachable")


def _parent_output(left: tuple[int, ...], right: tuple[int, ...]) -> _Output:
    return _Output(IV, tuple(left + right), 0, BLOCK_LEN, PARENT)


def digest(data: bytes) -> bytes:
    """Return the 32-byte unkeyed BLAKE3 digest for *data*."""
    chunk_count = max(1, (len(data) + CHUNK_LEN - 1) // CHUNK_LEN)
    cv_stack: list[tuple[int, ...]] = []

    for chunk_index in range(chunk_count - 1):
        chunk = data[chunk_index * CHUNK_LEN : (chunk_index + 1) * CHUNK_LEN]
        new_cv = _chunk_output(chunk, chunk_index).chaining_value()
        total_chunks = chunk_index + 1
        while total_chunks & 1 == 0:
            new_cv = _parent_output(cv_stack.pop(), new_cv).chaining_value()
            total_chunks >>= 1
        cv_stack.append(new_cv)

    final_index = chunk_count - 1
    final_chunk = data[final_index * CHUNK_LEN :]
    output = _chunk_output(final_chunk, final_index)
    while cv_stack:
        output = _parent_output(cv_stack.pop(), output.chaining_value())
    return output.root_bytes(32)


def hexdigest(data: bytes) -> str:
    return digest(data).hex()
