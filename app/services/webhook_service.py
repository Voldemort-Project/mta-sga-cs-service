"""Webhook service for handling WAHA messages"""
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.guest_repository import GuestRepository
from app.models.message import MessageRole
from app.models.session import SessionStatus, SessionMode
from app.integrations.waha import WahaService
from app.schemas.webhook import WahaWebhookRequest
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from app.utils.phone_utils import format_phone_international_id, format_phone_local_id

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for handling WAHA webhook events"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = GuestRepository(db)
        self.waha_service = WahaService()

    def _extract_phone_from_chat_id(self, chat_id: str) -> str:
        """
        Extract phone number from WhatsApp chatId.

        Args:
            chat_id: WhatsApp chatId (e.g., "6281234567890@c.us")

        Returns:
            Phone number without @c.us suffix
        """
        return chat_id.replace("@c.us", "")

    async def handle_incoming_message(self, webhook_data: WahaWebhookRequest) -> None:
        """
        Handle incoming message from guest.

        Args:
            webhook_data: Webhook data from WAHA
        """
        payload = webhook_data.payload

        # Ignore messages from ourselves
        if payload.fromMe:
            logger.info(f"Ignoring message from self: {payload.id}")
            return

        # Extract phone number from chatId
        phone_number = self._extract_phone_from_chat_id(payload.from_)

        # Format phone number to match database format (with leading 0)
        # Database stores: 081234567890
        # WAHA sends: 6281234567890@c.us
        phone_number = format_phone_local_id(phone_number)

        logger.info(f"Processing message from {phone_number}: {payload.body}")

        # Find user by phone number
        user = await self.repository.get_user_by_phone(phone_number)
        if not user:
            logger.warning(f"User not found for phone number: {phone_number}")
            return

        # Get active session for user
        session = await self.repository.get_active_session_by_user_id(user.id)
        if not session:
            logger.warning(f"No active session found for user: {user.id}")
            return

        try:
            # Save incoming message to database with User role
            await self.repository.create_message(
                session_id=session.id,
                role=MessageRole.User,
                text=payload.body or ""
            )

            # Prepare auto-reply message
            auto_reply_text = (
                "Terima kasih atas pesan Anda. 🙏\n\n"
                "Tim kami akan segera merespons pertanyaan Anda. "
                "Mohon menunggu sebentar.\n\n"
                "Waktu respon normal: 5-10 menit"
            )

            # Save auto-reply to database with System role
            await self.repository.create_message(
                session_id=session.id,
                role=MessageRole.System,
                text=auto_reply_text
            )

            # Commit database changes
            await self.db.commit()

            # Send auto-reply via WAHA (best effort, non-blocking)
            try:
                # Format phone number to international format (with 62 prefix)
                waha_phone = format_phone_international_id(phone_number)

                await self.waha_service.send_text_message(
                    phone_number=waha_phone,
                    text=auto_reply_text
                )
                logger.info(f"Auto-reply sent to {phone_number}")
            except Exception as e:
                logger.error(f"Failed to send auto-reply to {phone_number}: {str(e)}")
                # Don't fail the whole operation if sending fails

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error processing message from {phone_number}: {str(e)}")
            raise

    async def send_message(self, session_id: UUID, message: str) -> None:
        """
        Send message to user via WAHA and record it in database.

        Args:
            session_id: Session ID
            message: Message text to send

        Raises:
            ComposeError: If session not found, user not found, or user has no mobile phone
        """
        # Get session with user from repository
        session = await self.repository.get_session_with_user(session_id)

        if not session:
            raise ComposeError(
                error_code=ErrorCode.General.NOT_FOUND,
                message=f"Session {session_id} not found",
                http_status_code=404
            )

        if not session.user:
            raise ComposeError(
                error_code=ErrorCode.General.NOT_FOUND,
                message=f"User not found for session {session_id}",
                http_status_code=404
            )

        # Check if session status is terminated - if so, do nothing
        if session.status == SessionStatus.terminated:
            logger.info(f"Session {session_id} is terminated, skipping message send")
            return

        if not session.user.mobile_phone:
            raise ComposeError(
                error_code=ErrorCode.General.BAD_REQUEST,
                message=f"User {session.user.id} does not have a mobile phone number",
                http_status_code=400
            )

        try:
            # Record message in database with System role (only if mode is agent)
            if session.mode == SessionMode.agent:
                await self.repository.create_message(
                    session_id=session.id,
                    role=MessageRole.System,
                    text=message
                )
            else:
                logger.info(f"Session {session_id} mode is {session.mode}, not agent mode, skipping message record")

            # Format phone number to international format (with 62 prefix for Indonesia)
            waha_phone = format_phone_international_id(session.user.mobile_phone)

            # Send message via WAHA (always send, regardless of mode)
            await self.waha_service.send_text_message(
                phone_number=waha_phone,
                text=message
            )

            # Commit database changes
            await self.db.commit()

            logger.info(
                f"Message sent successfully to {session.user.mobile_phone} "
                f"for session {session_id}"
            )

        except ComposeError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error sending message for session {session_id}: {str(e)}", exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.General.INTERNAL_SERVER_ERROR,
                message=f"Failed to send message: {str(e)}",
                http_status_code=500,
                original_error=e
            )
