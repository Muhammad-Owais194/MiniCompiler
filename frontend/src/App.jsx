import React, { useState, useCallback } from "react";
import Editor from "@monaco-editor/react";
import { compile, run } from "./services/api";
import TokenTable from "./components/TokenTable";
import AstTree from "./components/AstTree";
import SymbolTableView from "./components/SymbolTable";

const SAMPLE = `#include <iostream>
using namespace std;

int add(int a, int b) {
    return a + b;
}

int main() {
    int x = 10;
    int y = 32;
    int z = add(x, y);

    if (z > 40) {
        cout << "big: " << z << endl;
    } else {
        cout << "small" << endl;
    }

    for (int i = 0; i < 3; i = i + 1) {
        cout << i << endl;
    }
    return 0;
}
`;

const TABS = [
  { key: "output", label: "Output" },
  { key: "tokens", label: "Tokens" },
  { key: "ast", label: "AST" },
  { key: "symbols", label: "Symbol Table" },
  { key: "bytecode", label: "IR / Bytecode" },
  { key: "errors", label: "Errors" },
];

export default function App() {
  const [code, setCode] = useState(SAMPLE);
  const [result, setResult] = useState(null);
  const [stdout, setStdout] = useState("");
  const [tab, setTab] = useState("output");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("Ready.");

  const doCompile = useCallback(async () => {
    setBusy(true); setStatus("Compiling…"); setStdout("");
    try {
      const r = await compile(code);
      setResult(r);
      setStatus(r.success ? "Compiled successfully." : `Compilation failed with ${r.errors.length} error(s).`);
      if (!r.success) setTab("errors");
    } catch (e) {
      setStatus(`Network error: ${e.message}`);
    } finally { setBusy(false); }
  }, [code]);

  const doRun = useCallback(async () => {
    setBusy(true); setStatus("Running…");
    try {
      const r = await run(code);
      setStdout(r.stdout || "");
      if (!r.success) {
        setResult((p) => ({ ...(p || {}), errors: r.errors, success: false }));
        setStatus(`Run failed.`);
        setTab("errors");
      } else {
        setStatus("Program exited normally.");
        setTab("output");
      }
    } catch (e) {
      setStatus(`Network error: ${e.message}`);
    } finally { setBusy(false); }
  }, [code]);

  const errCount = result?.errors?.length || 0;

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>C++ MiniCompiler</h1>
          <div className="subtitle">Lexer · Parser · Semantic · Symbol Table · Bytecode · VM</div>
        </div>
        <div className="subtitle">FastAPI + React</div>
      </header>

      <div className="toolbar">
        <button className="btn" onClick={doCompile} disabled={busy}>Compile</button>
        <button className="btn" onClick={doRun} disabled={busy}>Run</button>
        <button className="btn secondary" onClick={() => setTab("tokens")}>Tokens</button>
        <button className="btn secondary" onClick={() => setTab("ast")}>AST</button>
        <button className="btn secondary" onClick={() => setTab("symbols")}>Symbol Table</button>
        <button className="btn secondary" onClick={() => setTab("bytecode")}>IR</button>
        <button className="btn secondary" onClick={() => setTab("errors")}>
          Errors{errCount ? ` (${errCount})` : ""}
        </button>
      </div>

      <div className="main">
        <div className="pane">
          <div className="pane-header">Source — main.cpp</div>
          <div className="editor-wrap">
            <Editor
              height="100%"
              defaultLanguage="cpp"
              theme="vs"
              value={code}
              onChange={(v) => setCode(v || "")}
              options={{ fontSize: 13, minimap: { enabled: false }, scrollBeyondLastLine: false, automaticLayout: true }}
            />
          </div>
        </div>

        <div className="pane">
          <div className="tabs">
            {TABS.map((t) => (
              <div key={t.key}
                   className={`tab ${tab === t.key ? "active" : ""}`}
                   onClick={() => setTab(t.key)}>
                {t.label}
                {t.key === "errors" && errCount > 0 && <span className="badge">{errCount}</span>}
              </div>
            ))}
          </div>
          <div className="tab-content">
            {tab === "output" && <pre>{stdout || <em>Click “Run” to execute.</em>}</pre>}
            {tab === "tokens" && <TokenTable tokens={result?.tokens} />}
            {tab === "ast" && <AstTree ast={result?.ast} />}
            {tab === "symbols" && <SymbolTableView symbols={result?.symbol_table} />}
            {tab === "bytecode" && <pre>{result?.bytecode_text || <em>Compile first.</em>}</pre>}
            {tab === "errors" && (
              errCount === 0
                ? <em>No errors.</em>
                : <ul className="errors">{result.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
            )}
          </div>
        </div>
      </div>

      <div className={`status ${errCount ? "error" : ""}`}>{status}</div>
    </div>
  );
}
