from app.graph.planner.provider_enrichment import (
    ProviderEnrichmentOptions,
    build_module_outputs,
)
from app.schemas.trip_planning import TripConfiguration, TripModuleOutputs


QUICK_PLAN_PROVIDER_OPTIONS = ProviderEnrichmentOptions(
    request_timeout_seconds=3.0,
    parallel=True,
    flight_allow_live_fallback=False,
    flight_parameter_sets_limit=1,
    hotel_result_limit=6,
    hotel_rate_lookup_limit=0,
    hotel_include_llm_fallback=False,
    activity_category_limit=1,
)


def build_quick_plan_module_outputs(
    *,
    configuration: TripConfiguration,
    previous_configuration: TripConfiguration,
    existing_module_outputs: TripModuleOutputs,
    allowed_modules: set[str],
) -> TripModuleOutputs:
    return build_module_outputs(
        configuration,
        previous_configuration,
        existing_module_outputs,
        allowed_modules=allowed_modules,
        options=QUICK_PLAN_PROVIDER_OPTIONS,
    )
