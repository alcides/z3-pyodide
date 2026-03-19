"""Tests for BitVector operations."""

import pytest
from z3_pyodide import (
    BitVec, BitVecs, BitVecVal,
    Solver, sat, unsat,
    And, Or, Not, Distinct,
    UDiv, URem, SDiv, SRem, LShR,
    RotateLeft, RotateRight,
    ZeroExt, SignExt, Extract, Concat, RepeatBitVec,
    ULT, ULE, UGT, UGE,
    BV2Int, Int2BV,
    Int, IntVal,
    is_bv, is_bv_value,
    BitVecSort,
)


class TestBitVecBasic:
    def test_create_bitvec(self):
        x = BitVec("x", 8)
        assert is_bv(x)
        assert x.size() == 8
        assert x.sexpr() == "x"

    def test_bitvecs_constructor(self):
        x, y, z = BitVecs("x y z", 16)
        assert is_bv(x)
        assert x.size() == 16
        assert y.size() == 16

    def test_bitvecval(self):
        v = BitVecVal(42, 8)
        assert is_bv_value(v)
        assert v.as_long() == 42
        assert v.size() == 8
        assert v.sexpr() == "(_ bv42 8)"

    def test_bitvecval_negative(self):
        # -1 in 8 bits = 255
        v = BitVecVal(-1, 8)
        assert v.as_long() == 255
        assert v.as_signed_long() == -1

    def test_bitvecval_overflow(self):
        v = BitVecVal(256, 8)
        assert v.as_long() == 0  # wraps around

    def test_sort(self):
        x = BitVec("x", 32)
        assert x.sort() == BitVecSort(32)


class TestBitVecArithmetic:
    def test_add(self):
        x, y = BitVecs("x y", 8)
        s = Solver()
        s.add(x == BitVecVal(10, 8))
        s.add(y == BitVecVal(20, 8))
        s.add(x + y == BitVecVal(30, 8))
        assert s.check() == sat

    def test_add_overflow(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(255, 8))
        s.add(x + 1 == BitVecVal(0, 8))
        assert s.check() == sat

    def test_sub(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x - 1 == BitVecVal(9, 8))
        assert s.check() == sat
        assert s.model()[x].as_long() == 10

    def test_mul(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x * 3 == BitVecVal(12, 8))
        assert s.check() == sat
        assert s.model()[x].as_long() == 4

    def test_neg(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(5, 8))
        s.add(-x == BitVecVal(251, 8))  # -5 in 8-bit unsigned = 251
        assert s.check() == sat


class TestBitVecBitwise:
    def test_and(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b11001100, 8))
        s.add((x & BitVecVal(0b10101010, 8)) == BitVecVal(0b10001000, 8))
        assert s.check() == sat

    def test_or(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b11001100, 8))
        s.add((x | BitVecVal(0b10101010, 8)) == BitVecVal(0b11101110, 8))
        assert s.check() == sat

    def test_xor(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b11001100, 8))
        s.add((x ^ BitVecVal(0b10101010, 8)) == BitVecVal(0b01100110, 8))
        assert s.check() == sat

    def test_not(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b11001100, 8))
        s.add(~x == BitVecVal(0b00110011, 8))
        assert s.check() == sat

    def test_shift_left(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(1, 8))
        s.add((x << 3) == BitVecVal(8, 8))
        assert s.check() == sat

    def test_shift_right(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(8, 8))
        s.add((x >> 3) == BitVecVal(1, 8))
        assert s.check() == sat

    def test_lshr(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b10000000, 8))
        s.add(LShR(x, 1) == BitVecVal(0b01000000, 8))
        assert s.check() == sat


class TestBitVecComparisons:
    def test_signed_lt(self):
        x = BitVec("x", 8)
        s = Solver()
        # -1 (0xFF) < 0 in signed
        s.add(x == BitVecVal(255, 8))
        s.add(x < BitVecVal(0, 8))
        assert s.check() == sat

    def test_unsigned_lt(self):
        x = BitVec("x", 8)
        s = Solver()
        # 255 > 0 in unsigned
        s.add(x == BitVecVal(255, 8))
        s.add(ULT(x, BitVecVal(0, 8)))
        assert s.check() == unsat

    def test_ult(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(ULT(x, BitVecVal(5, 8)))
        s.add(UGT(x, BitVecVal(2, 8)))
        assert s.check() == sat
        val = s.model()[x].as_long()
        assert 2 < val < 5

    def test_equality(self):
        x, y = BitVecs("x y", 8)
        s = Solver()
        s.add(x == y)
        s.add(x == BitVecVal(42, 8))
        assert s.check() == sat
        assert s.model()[y].as_long() == 42


class TestBitVecExtractConcat:
    def test_extract(self):
        x = BitVec("x", 16)
        s = Solver()
        s.add(x == BitVecVal(0xABCD, 16))
        # Extract high byte (bits 15:8)
        s.add(Extract(15, 8, x) == BitVecVal(0xAB, 8))
        assert s.check() == sat

    def test_extract_low(self):
        x = BitVec("x", 16)
        s = Solver()
        s.add(x == BitVecVal(0xABCD, 16))
        s.add(Extract(7, 0, x) == BitVecVal(0xCD, 8))
        assert s.check() == sat

    def test_concat(self):
        a = BitVec("a", 8)
        b = BitVec("b", 8)
        s = Solver()
        s.add(a == BitVecVal(0xAB, 8))
        s.add(b == BitVecVal(0xCD, 8))
        s.add(Concat(a, b) == BitVecVal(0xABCD, 16))
        assert s.check() == sat

    def test_zero_ext(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0xFF, 8))
        s.add(ZeroExt(8, x) == BitVecVal(0x00FF, 16))
        assert s.check() == sat

    def test_sign_ext(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0xFF, 8))  # -1 signed
        s.add(SignExt(8, x) == BitVecVal(0xFFFF, 16))  # -1 sign-extended
        assert s.check() == sat


class TestBitVecDivision:
    def test_udiv(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(20, 8))
        s.add(UDiv(x, BitVecVal(4, 8)) == BitVecVal(5, 8))
        assert s.check() == sat

    def test_urem(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(20, 8))
        s.add(URem(x, BitVecVal(3, 8)) == BitVecVal(2, 8))
        assert s.check() == sat


class TestBitVecRotate:
    def test_rotate_left(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b10000001, 8))
        s.add(RotateLeft(x, 1) == BitVecVal(0b00000011, 8))
        assert s.check() == sat

    def test_rotate_right(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(0b10000001, 8))
        s.add(RotateRight(x, 1) == BitVecVal(0b11000000, 8))
        assert s.check() == sat


class TestBitVecModel:
    def test_model_extraction(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x == BitVecVal(42, 8))
        assert s.check() == sat
        m = s.model()
        val = m[x]
        assert val.as_long() == 42

    def test_model_multiple(self):
        x, y = BitVecs("x y", 8)
        s = Solver()
        s.add(x + y == BitVecVal(100, 8))
        s.add(x == BitVecVal(60, 8))
        assert s.check() == sat
        m = s.model()
        assert m[x].as_long() == 60
        assert m[y].as_long() == 40


class TestBitVecTypeChecking:
    def test_is_bv(self):
        x = BitVec("x", 8)
        assert is_bv(x)

    def test_is_bv_value(self):
        v = BitVecVal(42, 8)
        assert is_bv_value(v)

    def test_int_not_bv(self):
        x = Int("x")
        assert not is_bv(x)


class TestBitVecCoercion:
    def test_int_coercion(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(x + 1 == BitVecVal(43, 8))
        s.add(x == BitVecVal(42, 8))
        assert s.check() == sat

    def test_reverse_int_coercion(self):
        x = BitVec("x", 8)
        s = Solver()
        s.add(1 + x == BitVecVal(43, 8))
        s.add(x == BitVecVal(42, 8))
        assert s.check() == sat
