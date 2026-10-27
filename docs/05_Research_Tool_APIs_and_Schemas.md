# 05 — APIs, schemas and error behavior

## HTTP API
`GET /health` returns model adapter status and data manifest version; `GET /datasets` list and licenses; `GET /datasets/{id}/profile` count/variables/missingness; `POST /research-runs` objective + dataset + budget + seed; `GET /research-runs/{id}` status; `GET /research-runs/{id}/events` SSE; `GET /research-runs/{id}/artifacts`; `GET /research-runs/{id}/report`; `POST /research-runs/{id}/cancel`.

## Research request
`{objective:string, dataset_id:'ghana_combined'|'iita_drought'|'iita_full_irrigation'|'iita_multiloc'|'iita_striga', constraints:{max_steps:int,max_seconds:int}, seed:int}`. Validate length, enum and bounded budgets. Default to Ghana combined. Return run_id and immutable manifest hash.

## Tool call
See `schemas/agent_tool_call.schema.json`; action enum, version, dataset ID, typed parameters, hypothesis ID and trace ID. Reject unknown actions and extra fields; strict `additionalProperties:false`. No raw code execution.

## Tool result
See `schemas/research_result.schema.json`; provenance, results, uncertainty, warnings, and explicit `claim_scope` ('descriptive'|'exploratory'|'validated_model'). Return null rather than fabricated numeric values.

## Error catalog
400 malformed; 404 missing dataset; 409 incompatible datasets/units; 422 scientifically invalid query; 429 model budget; 503 model unavailable. Persist sanitized failure details and actionable retry instructions. API keys never appear in events.
