import { ResearchLinesInput } from "./ResearchLinesInput";
import { METHODS, OUTPUTS } from "./research-editor-types";
import type { ResearchConfiguration } from "./research-editor-types";

type Props = {
  value: ResearchConfiguration;
  onChange: (config: ResearchConfiguration) => void;
  disabled: boolean;
};
function toggle<T>(items: T[], item: T): T[] {
  return items.includes(item)
    ? items.filter((value) => value !== item)
    : [...items, item];
}

export function ResearchConfigurationPanel({
  value,
  onChange,
  disabled,
}: Readonly<Props>) {
  const update = (patch: Partial<ResearchConfiguration>) =>
    onChange({ ...value, ...patch });
  return (
    <details className="research-configuration">
      <summary>
        Optional research configuration{" "}
        <span>Questions, methods and execution limits</span>
      </summary>
      <div className="editor-configuration-fields">
        <label htmlFor="research-title">Research title</label>
        <input
          id="research-title"
          value={value.title}
          maxLength={200}
          disabled={disabled}
          onChange={(event) => update({ title: event.target.value })}
          placeholder="A short working title"
        />
        <ResearchLinesInput
          id="research-questions"
          label="Research questions · one per line, up to 20"
          value={value.research_questions}
          disabled={disabled}
          onChange={(questions) => update({ research_questions: questions })}
        />
        <ResearchLinesInput
          id="research-hypotheses"
          label="Proposed hypotheses · one per line, not results"
          value={value.hypotheses}
          disabled={disabled}
          onChange={(hypotheses) => update({ hypotheses })}
        />
        <fieldset className="editor-option-group">
          <legend>Dataset</legend>
          <button
            type="button"
            className="editor-option selected"
            aria-pressed={true}
            disabled={disabled}
            onClick={() => update({ dataset_id: "ghana_combined" })}
          >
            <strong>Ghana / WACCI combined</strong>
            <span>Analysis ready · source files remain immutable</span>
          </button>
          <p className="caption">
            IITA drought, irrigation, multi-location and Striga files are
            audited reference sources. They are not enabled as analysis-ready
            datasets. Genotype identifiers are not joined between experiments.
          </p>
        </fieldset>
        <fieldset className="editor-option-group">
          <legend>Preferred analysis methods</legend>
          <p className="caption">
            Leave these unselected for the supported default workflow.
          </p>
          <div className="editor-options-grid">
            {METHODS.map((method) => (
              <button
                key={method.id}
                type="button"
                className={`editor-option${value.preferred_methods.includes(method.id) ? " selected" : ""}`}
                aria-pressed={value.preferred_methods.includes(method.id)}
                disabled={disabled}
                onClick={() =>
                  update({
                    preferred_methods: toggle(
                      value.preferred_methods,
                      method.id,
                    ),
                  })
                }
              >
                <strong>{method.label}</strong>
                <span>{method.detail}</span>
              </button>
            ))}
          </div>
        </fieldset>
        <fieldset className="editor-option-group">
          <legend>Desired outputs</legend>
          <div className="editor-options-grid">
            {OUTPUTS.map((output) => (
              <button
                key={output}
                type="button"
                className="editor-output-choice"
                aria-pressed={value.desired_outputs.includes(output)}
                disabled={disabled}
                onClick={() =>
                  update({
                    desired_outputs: toggle(value.desired_outputs, output),
                  })
                }
              >
                {output.replaceAll("_", " ")}
              </button>
            ))}
          </div>
        </fieldset>
        <fieldset className="editor-option-group">
          <legend>Research constraints</legend>
          <div className="editor-budget-grid">
            {(
              [
                ["max_steps", "Analysis steps", 6],
                ["max_tool_calls", "Tool calls", 10],
                ["max_seconds", "Seconds", 180],
              ] as const
            ).map(([key, label, maximum]) => (
              <label key={key}>
                <span>
                  {label} · 1–{maximum}
                </span>
                <input
                  inputMode="numeric"
                  pattern="[0-9]*"
                  value={value.constraints[key]}
                  disabled={disabled}
                  onChange={(event) =>
                    update({
                      constraints: {
                        ...value.constraints,
                        [key]: Number(event.target.value),
                      },
                    })
                  }
                />
              </label>
            ))}
          </div>
        </fieldset>
        <fieldset className="editor-option-group">
          <legend>Autonomous execution preferences</legend>
          {(
            [
              [
                "auto_plan_with_meta",
                "Plan with Meta in live mode",
                "Creates a structured plan from the full objective before bounded execution",
              ],
              [
                "execute_supported_tasks",
                "Execute supported analyses",
                "Turn off to prepare a plan without calculating scientific results",
              ],
              [
                "stop_if_unsupported",
                "Stop when a requested operation is unsupported",
                "Otherwise continue supported operations and report the unmet requirements",
              ],
            ] as const
          ).map(([key, title, description]) => (
            <button
              key={key}
              type="button"
              className="editor-option preference-option"
              aria-pressed={value.autonomy_preferences[key]}
              disabled={disabled}
              onClick={() =>
                update({
                  autonomy_preferences: {
                    ...value.autonomy_preferences,
                    [key]: !value.autonomy_preferences[key],
                  },
                })
              }
            >
              <strong>{title}</strong>
              <span>{description}</span>
              <b>{value.autonomy_preferences[key] ? "On" : "Off"}</b>
            </button>
          ))}
        </fieldset>
      </div>
    </details>
  );
}
