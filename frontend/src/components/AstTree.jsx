import React from "react";

function Node({ node }) {
  if (node === null || node === undefined) return <span className="node-meta">null</span>;
  if (typeof node !== "object") return <span>{String(node)}</span>;
  if (Array.isArray(node)) {
    if (node.length === 0) return <span className="node-meta">[]</span>;
    return (
      <ul>
        {node.map((c, i) => <li key={i}><Node node={c} /></li>)}
      </ul>
    );
  }
  const { node: name, line, ...rest } = node;
  const fields = Object.entries(rest);
  return (
    <div>
      <span className="node-name">{name || "Object"}</span>
      {line ? <span className="node-meta"> (line {line})</span> : null}
      {fields.length > 0 && (
        <ul>
          {fields.map(([k, v]) => (
            <li key={k}>
              <span className="node-meta">{k}: </span>
              <Node node={v} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function AstTree({ ast }) {
  if (!ast) return <em>No AST.</em>;
  return <div className="tree"><Node node={ast} /></div>;
}
