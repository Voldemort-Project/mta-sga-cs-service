"""Webhook service for handling WAHA messages"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.guest_repository import GuestRepository
from app.models.message import MessageRole
from app.integrations.waha import WahaService
from app.schemas.webhook import WahaWebhookRequest

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
        if phone_number.startswith("62"):
            phone_number = "0" + phone_number[2:]

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
                # Send with original phone format that WAHA expects (with 62 prefix)
                original_phone = phone_number
                if original_phone.startswith("0"):
                    original_phone = "62" + original_phone[1:]

                await self.waha_service.send_text_message(
                    phone_number=original_phone,
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
