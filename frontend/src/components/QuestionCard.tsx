import { Check, X } from "lucide-react";
import { SourcesPanel } from "@/components/SourcesPanel";
import { cn } from "@/lib/cn";
import type { Choice, ExamQuestion } from "@/types/api";

const CHOICES: Choice[] = ["A", "B", "C", "D"];

interface QuestionCardProps {
  question: ExamQuestion;
  index: number;
  selected: Choice | null;
  onSelect: (choice: Choice) => void;
  /** When set, the question is graded: reveal correct answer + explanation. */
  graded?: boolean;
}

export function QuestionCard({ question, index, selected, onSelect, graded }: QuestionCardProps) {
  return (
    <fieldset className="space-y-3" disabled={graded}>
      <legend className="mb-1 font-medium">
        <span className="text-muted-foreground">Q{index + 1}.</span> {question.stem}
      </legend>
      <div className="grid gap-2">
        {CHOICES.map((c) => {
          const text = question.options[c];
          if (text === undefined) return null;
          const isSelected = selected === c;
          const isCorrect = question.correct === c;
          const showCorrect = graded && isCorrect;
          const showWrong = graded && isSelected && !isCorrect;
          return (
            <label
              key={c}
              className={cn(
                "flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors",
                !graded && "hover:bg-muted/60",
                isSelected && !graded && "border-primary bg-primary-soft",
                !isSelected && !graded && "border-input",
                showCorrect && "border-success bg-success-soft",
                showWrong && "border-danger bg-danger-soft",
                graded && !showCorrect && !showWrong && "border-input opacity-70",
              )}
            >
              <input
                type="radio"
                name={question.id}
                value={c}
                checked={isSelected}
                onChange={() => onSelect(c)}
                className="sr-only"
              />
              <span
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
                  isSelected ? "border-primary bg-primary text-primary-foreground" : "border-input",
                )}
                aria-hidden
              >
                {showCorrect ? (
                  <Check className="size-4" />
                ) : showWrong ? (
                  <X className="size-4" />
                ) : (
                  c
                )}
              </span>
              <span className="pt-0.5">{text}</span>
            </label>
          );
        })}
      </div>
      {graded && (
        <div className="rounded-lg bg-muted/60 p-3 text-sm">
          <p className="mb-2">
            <span className="font-semibold">Explanation. </span>
            {question.explanation}
          </p>
          <SourcesPanel sources={question.sources} />
        </div>
      )}
    </fieldset>
  );
}
