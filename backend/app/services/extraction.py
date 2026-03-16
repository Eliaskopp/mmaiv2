import logging
import uuid

from app.core.database import async_session
from app.schemas.note import NoteExtraction
from app.services.grok import GrokClient
from app.services import note as note_service

logger = logging.getLogger(__name__)


async def extract_and_save_notes(
    assistant_content: str,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> None:
    """Extract actionable notes from an assistant response and save them.

    Runs as a background task — creates its own DB session since the
    request session is closed by the time this executes.
    Failures are logged but never raised.
    """
    try:
        grok = GrokClient()
        raw = await grok.extract_notes(assistant_content)
        if raw is None:
            return

        extraction = NoteExtraction(**raw)
        if not extraction.has_extractable_content:
            return

        data = {
            "type": extraction.type,
            "title": extraction.title,
            "summary": extraction.summary,
        }

        async with async_session() as db:
            await note_service.create_ai_note(db, user_id, data, conversation_id)

    except Exception:
        logger.exception("Background note extraction failed")
