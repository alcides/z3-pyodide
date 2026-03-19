#!/bin/bash
# Downloads Z3 WASM files for local serving.
# Uses cpitclaudel/z3.wasm — a single-threaded build that works
# without SharedArrayBuffer/Web Workers.
# Run once before starting the server.

set -e
cd "$(dirname "$0")"

BASE_URL="https://people.csail.mit.edu/cpitcla/z3.wasm"

echo "Downloading Z3 WASM (single-threaded build)..."

if [ ! -f "z3w.js" ]; then
    echo "  z3w.js (~132 KB)..."
    curl -sL "${BASE_URL}/z3w.js" -o z3w.js
else
    echo "  z3w.js (already exists)"
fi

if [ ! -f "z3w.wasm" ]; then
    echo "  z3w.wasm (~17 MB, this may take a moment)..."
    curl -sL "${BASE_URL}/z3w.wasm" -o z3w.wasm
else
    echo "  z3w.wasm (already exists)"
fi

echo "Done! Now run: python3 examples/server.py"
