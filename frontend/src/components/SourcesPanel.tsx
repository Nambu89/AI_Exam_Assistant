import { FileText } from "lucide-react";

interface SourcesPanelProps {
  sources: string[];
}

/** Shows the corpus sources an answer/question was grounded in. */
export function SourcesPanel({ sources }: SourcesPanelProps) {
  if (sources.length === 0) {
    return <p className="text-sm text-muted-foreground">No sources cited yet.</p>;
  }
  return (
    <ul className="flex flex-col gap-2">
      {sources.map((src) => {
        const [file, section] = src.split("#");
        return (
          <li key={src} className="flex items-start gap-2 text-sm">
            <FileText className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden />
            <span className="min-w-0">
              <span className="break-words font-medium">{section ?? file}</span>
              {section && (
                <span className="block truncate text-xs text-muted-foreground">{file}</span>
              )}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
