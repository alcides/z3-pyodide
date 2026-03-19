// Web Worker that loads Z3 WASM and handles eval_smtlib2_string requests.
// Z3 runs in this worker thread so it doesn't block the main thread.
//
// Each eval call creates a FRESH Z3 module instance because the old
// Emscripten build's callMain() cannot be called multiple times
// (exit() corrupts internal state). The WASM binary is compiled once
// and cached by the browser, so re-instantiation is fast (~50ms).

importScripts('z3w.js');

let ready = false;
let wasmBinaryCache = null;

function loadSolver() {
    // Do a warm-up instantiation to trigger WASM compilation & cache
    const warmup = Z3({
        ENVIRONMENT: 'WORKER',
        noInitialRun: true,
        print: function() {},
        printErr: function() {},
    });
    // Warm-up call to fully initialize
    warmup.FS.writeFile('/warmup.smt2', '(check-sat)\n');
    try { warmup.callMain(['/warmup.smt2']); } catch(e) {}

    ready = true;
    postMessage({ kind: 'ready' });
}

function runSolver(commands) {
    // Create a fresh module for each call (WASM binary is cached by browser)
    let stdoutBuf = [];
    const solver = Z3({
        ENVIRONMENT: 'WORKER',
        noInitialRun: true,
        print: function(text) { stdoutBuf.push(text); },
        printErr: function(text) { /* suppress */ },
    });

    solver.FS.writeFile('/input.smt2', commands);
    try {
        solver.callMain(['/input.smt2']);
    } catch (e) {
        // callMain throws on exit(0), expected
    }
    return stdoutBuf.join('\n');
}

self.onmessage = function(event) {
    const { kind, payload, id } = event.data;
    if (kind === 'init') {
        loadSolver();
    } else if (kind === 'eval') {
        const result = runSolver(payload);
        postMessage({ kind: 'result', id: id, payload: result });
    }
};
