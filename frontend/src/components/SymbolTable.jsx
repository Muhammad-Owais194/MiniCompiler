import React from "react";

export default function SymbolTable({ symbols }) {
  if (!symbols?.length) return <em>No symbols.</em>;
  return (
    <table>
      <thead>
        <tr><th>Name</th><th>Kind</th><th>Type</th><th>Scope</th><th>Line</th></tr>
      </thead>
      <tbody>
        {symbols.map((s, i) => (
          <tr key={i}>
            <td>{s.name}</td><td>{s.kind}</td><td>{s.type}</td>
            <td>{s.scope}</td><td>{s.line}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
