"use client";
import { useEffect, useRef, useState } from "react";
import { textLines } from "./research-editor-types";

type Props = {
  id: string;
  label: string;
  value: string[];
  onChange: (value: string[]) => void;
  disabled?: boolean;
};
export function ResearchLinesInput({
  id,
  label,
  value,
  onChange,
  disabled,
}: Readonly<Props>) {
  const [writing, setWriting] = useState(value.join("\n"));
  const lastSent = useRef(value.join("\n"));
  useEffect(() => {
    const incoming = value.join("\n");
    if (incoming !== lastSent.current) {
      lastSent.current = incoming;
      setWriting(incoming);
    }
  }, [value]);
  return (
    <div className="research-lines-input">
      <label htmlFor={id}>{label}</label>
      <textarea
        id={id}
        rows={3}
        value={writing}
        disabled={disabled}
        onChange={(event) => {
          const raw = event.target.value;
          const lines = textLines(raw);
          lastSent.current = lines.join("\n");
          setWriting(raw);
          onChange(lines);
        }}
      />
    </div>
  );
}
