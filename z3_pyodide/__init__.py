"""z3-pyodide: Z3 theorem prover API compatible with Pyodide."""

from ._exprs import (
    ExprRef,
    BoolRef,
    ArithRef,
    IntNumRef,
    RatNumRef,
    BoolValRef,
    BitVecRef,
    BitVecNumRef,
    ArrayRef,
    DatatypeRef,
    Z3Exception,
)
from ._sorts import (
    SortRef,
    BoolSortRef,
    ArithSortRef,
    BitVecSortRef,
    ArraySortRef,
    BoolSort,
    IntSort,
    RealSort,
    BitVecSort,
    ArraySort,
)
from ._solver import (
    Solver,
    Optimize,
    OptimizeObjective,
    CheckSatResult,
    sat,
    unsat,
    unknown,
    simplify,
)
from ._model import ModelRef
from ._functions import (
    FuncDeclRef,
    Function,
    ForAll,
    Exists,
    QuantifierRef,
)
from ._datatypes import (
    Datatype,
    CreateDatatypes,
    DatatypeSortRef,
)
from ._toplevel import (
    Int,
    Ints,
    IntVal,
    Real,
    Reals,
    RealVal,
    Bool,
    Bools,
    BoolVal,
    And,
    Or,
    Not,
    Implies,
    Xor,
    If,
    Distinct,
    Sum,
    Product,
    ToReal,
    ToInt,
    IsInt,
    Abs,
    BitVec,
    BitVecs,
    BitVecVal,
    UDiv,
    URem,
    SDiv,
    SRem,
    LShR,
    RotateLeft,
    RotateRight,
    ZeroExt,
    SignExt,
    Extract,
    Concat,
    RepeatBitVec,
    ULT,
    ULE,
    UGT,
    UGE,
    BV2Int,
    Int2BV,
    Array,
    Select,
    Store,
    K,
    is_array,
    Datatype,
    CreateDatatypes,
    is_bv,
    is_bv_value,
    is_bool,
    is_int,
    is_real,
    is_int_value,
    is_rational_value,
)
from ._context import (
    Context,
    get_default_context,
    set_default_context,
    reset_default_context,
)

__version__ = "0.1.0"

__all__ = [
    # Expressions
    "ExprRef", "BoolRef", "ArithRef", "IntNumRef", "RatNumRef", "BoolValRef",
    "BitVecRef", "BitVecNumRef", "ArrayRef", "DatatypeRef",
    # Sorts
    "SortRef", "BoolSortRef", "ArithSortRef", "BitVecSortRef", "ArraySortRef",
    "BoolSort", "IntSort", "RealSort", "BitVecSort", "ArraySort",
    # Solver
    "Solver", "Optimize", "OptimizeObjective", "CheckSatResult",
    "sat", "unsat", "unknown", "simplify",
    # Model
    "ModelRef",
    # Constructors
    "Int", "Ints", "IntVal", "Real", "Reals", "RealVal",
    "Bool", "Bools", "BoolVal",
    "BitVec", "BitVecs", "BitVecVal",
    # Functions
    "FuncDeclRef", "Function", "ForAll", "Exists", "QuantifierRef",
    # Logical
    "And", "Or", "Not", "Implies", "Xor", "If", "Distinct",
    # Arithmetic
    "Sum", "Product", "Abs",
    # Conversions
    "ToReal", "ToInt", "IsInt",
    # BitVector operations
    "UDiv", "URem", "SDiv", "SRem", "LShR",
    "RotateLeft", "RotateRight",
    "ZeroExt", "SignExt", "Extract", "Concat", "RepeatBitVec",
    "ULT", "ULE", "UGT", "UGE",
    "BV2Int", "Int2BV",
    # Arrays
    "Array", "Select", "Store", "K", "is_array",
    # Datatypes
    "Datatype", "CreateDatatypes", "DatatypeSortRef",
    # Predicates
    "is_bv", "is_bv_value",
    "is_bool", "is_int", "is_real", "is_int_value", "is_rational_value",
    # Context
    "Context", "get_default_context", "set_default_context", "reset_default_context",
    # Exceptions
    "Z3Exception",
    # Version
    "__version__",
]
