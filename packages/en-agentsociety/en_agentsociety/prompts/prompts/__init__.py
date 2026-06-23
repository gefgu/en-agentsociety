"""
Python prompt class registry.

Each domain module in this package defines one or more ``BasePrompt`` subclasses
that replace the corresponding TOML prompt file(s).  This module collects all
registered classes and exports ``_ALL_PROMPT_CLASSES`` for use by
``PromptManager._resolve_and_load_classes``.
"""
from ..base import BasePrompt

# --- Batch 1: simple time-estimate prompts ---
from .otherblock import (
    OtherSleepTimeEstimateAgentsociety,
    OtherSleepTimeEstimateCitysim,
    OtherTimeEstimateAgentsociety,
    OtherTimeEstimateCitysim,
)
from .socialblock import (
    SocialTimeEstimateAgentsociety,
    SocialTimeEstimateCitysim,
)

# --- Batch 2: worktime, social message generation, plan guidance ---
from .economyblock import (
    WorktimeEstimateAgentsociety,
    WorktimeEstimateCitysim,
)
from .socialblock import (
    SocialMessageGenerationAgentsociety,
    SocialMessageGenerationCitysim,
)
from .planblock import (
    PlanGuidanceSelectionAgentsociety,
    PlanGuidanceSelectionCitysim,
)

# --- Batch 3: block dispatcher ---
from .agent import (
    BlockDispatcherAgentsociety,
    BlockDispatcherCitysim,
)

# --- Batch 4: cognition init + needs init ---
from .cognitionblock import (
    CognitionAttitudeUpdateAgentsociety,
    CognitionAttitudeUpdateCitysim,
    CognitionEmotionUpdateAgentsociety,
    CognitionEmotionUpdateCitysim,
    CognitionThoughtUpdateAgentsociety,
    CognitionThoughtUpdateCitysim,
    CognitionInitializeBig5Citysim,
    CognitionInitializeHobbiesCitysim,
    CognitionInitializePreferencesCitysim,
)
from .needsblock import (
    NeedsEvaluationAgentsociety,
    NeedsEvaluationCitysim,
    NeedsInitializeAgentsociety,
    NeedsInitializeCitysim,
    NeedsPoiObservationCitysim,
    NeedsReflectionAgentsociety,
    NeedsReflectionCitysim,
)

# --- Batch 5: mobility prompts ---
from .mobilityblock import (
    MobilityAoiAreaSelectionAgentsociety,
    MobilityAoiAreaSelectionCitysim,
    MobilityNeighborhoodSelectionAgentsociety,
    MobilityNeighborhoodSelectionCitysim,
    MobilityPlaceAnalysisAgentsociety,
    MobilityPlaceAnalysisCitysim,
    MobilityPlaceTypeSelectionAgentsociety,
    MobilityPlaceTypeSelectionCitysim,
    MobilityPlaceSecondTypeSelectionAgentsociety,
    MobilityPlaceSecondTypeSelectionCitysim,
    MobilityRadiusSelectionAgentsociety,
    MobilityRadiusSelectionCitysim,
    MobilityTransportModeSelectionCitysim,
)

# --- Batch 6: daily schedule block ---
from .dailyscheduleblock import (
    DailyScheduleGenerationAgentsociety,
    DailyScheduleGenerationCitysim,
    EmptyBlockFillingAgentsociety,
    EmptyBlockFillingCitysim,
)

# --- Batch 7: plan detailed generation ---
from .planblock import (
    PlanDetailedGenerationAgentsociety,
    PlanDetailedGenerationCitysim,
)

# --- Batch 8: economy monthly plan prompts ---
from .economyblock import (
    MonthPlanGoalCreationAgentsociety,
    MonthPlanGoalCreationCitysim,
    MonthPlanMentalHealthAssessmentAgentsociety,
    MonthPlanMentalHealthAssessmentCitysim,
    MonthPlanObservationAgentsociety,
    MonthPlanObservationCitysim,
)

# --- Batch 9: societyagent prompts ---
from .societyagent import (
    SocietyAgentEnvironmentReflectionAgentsociety,
    SocietyAgentEnvironmentReflectionCitysim,
    SocietyAgentStatusSummaryAgentsociety,
    SocietyAgentStatusSummaryCitysim,
    SocietyAgentChatResponseDecisionAgentsociety,
    SocietyAgentChatResponseDecisionCitysim,
    SocietyAgentChatBeliefUpdateAgentsociety,
    SocietyAgentChatBeliefUpdateCitysim,
)

_ALL_PROMPT_CLASSES: list[type[BasePrompt]] = [
    # --- Batch 1 ---
    OtherSleepTimeEstimateAgentsociety,
    OtherSleepTimeEstimateCitysim,
    OtherTimeEstimateAgentsociety,
    OtherTimeEstimateCitysim,
    SocialTimeEstimateAgentsociety,
    SocialTimeEstimateCitysim,
    # --- Batch 2 ---
    WorktimeEstimateAgentsociety,
    WorktimeEstimateCitysim,
    SocialMessageGenerationAgentsociety,
    SocialMessageGenerationCitysim,
    PlanGuidanceSelectionAgentsociety,
    PlanGuidanceSelectionCitysim,
    # --- Batch 3 ---
    BlockDispatcherAgentsociety,
    BlockDispatcherCitysim,
    # --- Batch 4 ---
    CognitionAttitudeUpdateAgentsociety,
    CognitionAttitudeUpdateCitysim,
    CognitionEmotionUpdateAgentsociety,
    CognitionEmotionUpdateCitysim,
    CognitionThoughtUpdateAgentsociety,
    CognitionThoughtUpdateCitysim,
    CognitionInitializeBig5Citysim,
    CognitionInitializeHobbiesCitysim,
    CognitionInitializePreferencesCitysim,
    NeedsEvaluationAgentsociety,
    NeedsEvaluationCitysim,
    NeedsInitializeAgentsociety,
    NeedsInitializeCitysim,
    NeedsPoiObservationCitysim,
    NeedsReflectionAgentsociety,
    NeedsReflectionCitysim,
    # --- Batch 5 ---
    MobilityAoiAreaSelectionAgentsociety,
    MobilityAoiAreaSelectionCitysim,
    MobilityNeighborhoodSelectionAgentsociety,
    MobilityNeighborhoodSelectionCitysim,
    MobilityPlaceAnalysisAgentsociety,
    MobilityPlaceAnalysisCitysim,
    MobilityPlaceTypeSelectionAgentsociety,
    MobilityPlaceTypeSelectionCitysim,
    MobilityPlaceSecondTypeSelectionAgentsociety,
    MobilityPlaceSecondTypeSelectionCitysim,
    MobilityRadiusSelectionAgentsociety,
    MobilityRadiusSelectionCitysim,
    MobilityTransportModeSelectionCitysim,
    # --- Batch 6 ---
    DailyScheduleGenerationAgentsociety,
    DailyScheduleGenerationCitysim,
    EmptyBlockFillingAgentsociety,
    EmptyBlockFillingCitysim,
    # --- Batch 7 ---
    PlanDetailedGenerationAgentsociety,
    PlanDetailedGenerationCitysim,
    # --- Batch 8 ---
    MonthPlanGoalCreationAgentsociety,
    MonthPlanGoalCreationCitysim,
    MonthPlanMentalHealthAssessmentAgentsociety,
    MonthPlanMentalHealthAssessmentCitysim,
    MonthPlanObservationAgentsociety,
    MonthPlanObservationCitysim,
    # --- Batch 9 ---
    SocietyAgentEnvironmentReflectionAgentsociety,
    SocietyAgentEnvironmentReflectionCitysim,
    SocietyAgentStatusSummaryAgentsociety,
    SocietyAgentStatusSummaryCitysim,
    SocietyAgentChatResponseDecisionAgentsociety,
    SocietyAgentChatResponseDecisionCitysim,
    SocietyAgentChatBeliefUpdateAgentsociety,
    SocietyAgentChatBeliefUpdateCitysim,
]
