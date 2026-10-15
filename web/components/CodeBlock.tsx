export function CodeBlock({
  code,
  labelledBy,
}: {
  code: string;
  labelledBy: string;
}) {
  return (
    <pre className="code-block" tabIndex={0} aria-labelledby={labelledBy}>
      <code>{code}</code>
    </pre>
  );
}
