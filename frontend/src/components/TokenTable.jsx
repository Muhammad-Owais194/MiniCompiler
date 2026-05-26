import React from "react";

export default function TokenTable({ tokens }) {
  if (!tokens?.length) return <em>No tokens.</em>;
  return (
    <table>
      <thead>
        <tr><th>#</th><th>Type</th><th>Lexeme</th><th>Value</th><th>Line</th><th>Col</th></tr>
      </thead>
      <tbody>
        {tokens.map((t, i) => (
          <tr key={i}>
            <td>{i}</td><td>{t.type}</td><td>{t.lexeme}</td>
            <td>{t.value === null ? "" : String(t.value)}</td>
            <td>{t.line}</td><td>{t.col}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
