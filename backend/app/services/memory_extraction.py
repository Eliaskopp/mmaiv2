import logging
import uuid

from pydantic import ValidationError

from app.schemas.memory import PerformanceEventExtraction, UserTrainingStateExtraction
from app.services import memory as memory_service
from app.services.grok import GrokClient

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6


async def extract_and_save_memory(
    db_session_maker,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    user_content: str,
    assistant_content: str,
) -> None:
    """Extract structured performance data from a conversation and persist it.

    Runs as a background task — creates its own DB session via the
    provided session factory since the request session is closed by
    the time this executes.
    Failures are logged but never raised.
    """
    try:
        messages = [
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": assistant_content},
        ]

        grok = GrokClient()
        raw = await grok.extract_memory(messages)
        if raw is None:
            return

        # Validate and filter performance events by confidence threshold
        validated_events: list[PerformanceEventExtraction] = []
        for event_dict in raw.get("performance_events", []):
            try:
                extraction = PerformanceEventExtraction(**event_dict)
            except ValidationError:
                logger.warning(
                    "Skipping malformed performance event for user=%s: %s",
                    user_id,
                    event_dict,
                )
                continue
            if extraction.extraction_confidence >= CONFIDENCE_THRESHOLD:
                validated_events.append(extraction)

        # Validate training state if present
        validated_state: UserTrainingStateExtraction | None = None
        raw_state = raw.get("training_state")
        if raw_state is not None:
            try:
                validated_state = UserTrainingStateExtraction(**raw_state)
            except ValidationError:
                logger.warning(
                    "Skipping malformed training state for user=%s: %s",
                    user_id,
                    raw_state,
                )

        # Only open a DB session if there's something to save
        if not validated_events and validated_state is None:
            return

        async with db_session_maker() as db:
            if validated_events:
                await memory_service.save_performance_events(
                    db, user_id, conversation_id, validated_events,
                )
            if validated_state:
                await memory_service.upsert_training_state(
                    db, user_id, validated_state,
                )

    except Exception:
        logger.exception("Background memory extraction failed")
