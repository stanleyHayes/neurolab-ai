"""Bounded job execution, shared by HTTP wakeups and the standalone worker."""

from __future__ import annotations

import time

from .agent import ResearchAgent
from .jobs import LeaseCheckedAdapter
from .model_spend import ModelSpendError
from .planner import refine_plan
from .providers import ModelProviderError, OpenAICompatibleAdapter
from .research_context import (
    ResearchConfiguration,
    ResearchRunRequest,
    build_deterministic_plan,
    objective_digest,
)
from .store import ExecutionCancelled, ExecutionLeaseLost


def execute_run(
    store,
    dataset,
    request: ResearchRunRequest,
    run_id: str,
    *,
    adapter_factory=OpenAICompatibleAdapter.from_environment,
) -> None:
    try:
        started = time.monotonic()
        configuration = request.configuration or ResearchConfiguration(
            dataset_id=request.dataset_id, constraints=request.constraints
        )
        store.assert_execution_lease()
        persisted = store.get_run(run_id)
        if persisted["source_sha256"] != dataset.source_sha256:
            raise ValueError(
                "Queued source bytes differ from the loaded dataset; no provider or tool was invoked"
            )
        if store.cancel_requested(run_id):
            store.add_event(run_id, "run.cancelled", {"reason": "cancelled_before_planning"})
            return
        model = adapter_factory() if request.mode == "meta" else None
        if isinstance(model, OpenAICompatibleAdapter):
            model.bind_spending(store, persisted["owner_user_id"], "run:" + run_id)
        adapter = LeaseCheckedAdapter(model, store, run_id) if model else None
        plan = request.plan or build_deterministic_plan(request.objective, configuration)
        if (
            adapter
            and request.plan is None
            and configuration.autonomy_preferences.auto_plan_with_meta
        ):
            store.add_event(
                run_id,
                "planning.requested",
                {
                    "provider": adapter.provider,
                    "model_id": adapter.model_id,
                    "objective_sha256": objective_digest(request.objective),
                },
            )
            plan = refine_plan(
                request.objective,
                configuration,
                adapter,
                timeout=min(45, configuration.constraints.max_seconds),
            )
            store.update_research_plan(run_id, plan.model_dump(mode="json"))
            store.add_event(
                run_id,
                "planning.completed",
                {
                    "provider": adapter.provider,
                    "model_id": adapter.model_id,
                    "task_count": len(plan.tasks),
                    "unsupported_requirements": plan.unsupported_requirements,
                },
            )
        remaining = configuration.constraints.max_seconds - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("Research planning exhausted the run time budget before analysis")
        agent = ResearchAgent(
            dataset,
            store,
            max_steps=configuration.constraints.max_steps,
            max_tool_calls=configuration.constraints.max_tool_calls,
            max_wall_time=remaining,
            mode=request.mode,
            model_adapter=adapter,
            configuration=configuration,
            research_plan=plan,
        )
        agent.run(request.objective, seed=request.seed, run_id=run_id)
    except ExecutionLeaseLost:
        raise
    except ExecutionCancelled:
        store.add_event(run_id, "run.cancelled", {"reason": "cancelled_before_provider_action"})
    except Exception as exc:
        sanitized = (
            str(exc)
            if isinstance(exc, (ModelProviderError, ModelSpendError, TimeoutError, ValueError))
            else (
                "Unexpected research execution error; inspect server logs without exposing secrets."
            )
        )
        store.add_event(
            run_id,
            "run.failed",
            {
                "error_type": type(exc).__name__,
                "message": sanitized[:200],
                "retryable": isinstance(exc, ModelProviderError),
            },
        )
