"""Webhook service for handling WAHA messages"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

from app.repositories.guest_repository import GuestRepository
from app.models.message import MessageRole
from app.models.session import SessionStatus, SessionMode
from app.integrations.waha import WahaService
from app.integrations.h2h import H2HAgentRouterService
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
        self.h2h_service = H2HAgentRouterService()

    def _extract_phone_from_chat_id(self, chat_id: str) -> str:
        """
        Extract phone number from WhatsApp chatId.

        Args:
            chat_id: WhatsApp chatId (e.g., "6281234567890@c.us")

        Returns:
            Phone number without @c.us suffix
        """
        return chat_id.replace("@c.us", "")

    async def _send_welcome_message(self, session_id: UUID, phone_number: str, user_name: str) -> None:
        """
        Send welcome message to user asking for category selection.

        Args:
            session_id: Session ID
            phone_number: User's phone number (in local format)
            user_name: User's name for welcome message
        """
        # Prepare welcome message
        welcome_text = (
            f"Halo {user_name}! 👋\n\n"
            f"Selamat datang kembali! Kami siap membantu Anda.\n\n"
            f"Pilih Salah 1 Kategori dibawah:\n"
            f"1. General Information\n"
            f"2. Room Service\n"
            f"3. Customer Service\n\n"
            f"Silahkan kirim 1, 2, atau 3 untuk memilih kategori yang Anda inginkan.\n"
            f"Ketik `/end` untuk mengakhiri percakapan.\n\n"
            f"Terima kasih! 🏨"
        )

        try:
            # Save welcome message to database with System role
            await self.repository.create_message(
                session_id=session_id,
                role=MessageRole.System,
                text=welcome_text
            )

            # Commit message
            await self.db.commit()

            # Send welcome message via WAHA
            waha_phone = format_phone_international_id(phone_number)
            await self.waha_service.send_text_message(
                phone_number=waha_phone,
                text=welcome_text
            )
            logger.info(f"Welcome message sent to {phone_number}")
        except Exception as e:
            logger.error(f"Failed to send welcome message to {phone_number}: {str(e)}")
            # Don't fail the operation if welcome message fails

    def _parse_category_command(self, message_text: str) -> Optional[str]:
        """
        Parse user message to extract category command.

        Args:
            message_text: User's message text

        Returns:
            Category string or None if not a valid command
        """
        message_text = message_text.strip()

        category_map = {
            "1": "general_information",
            "2": "room_service",
            "3": "customer_service"
        }

        return category_map.get(message_text)

    async def _send_h2h_message_background(self, session_id: UUID, message: str, phone_number: str) -> None:
        """
        Send message to H2H service in background and forward response to guest via WAHA.
        This method is run as a background task.

        Args:
            session_id: Session ID
            message: Message text to send
            phone_number: Guest's phone number (local format with leading 0)
        """
        try:
            # Send message to H2H and get response
            result = await self.h2h_service.send_chat_message(session_id, message)
            logger.info(f"H2H chat message sent successfully for session {session_id}: {result}")

            # Extract reply message from H2H response
            # Check various possible fields where the response message might be
            reply_message = None
            if isinstance(result, dict):
                # Common field names for response message
                res_data = result.get("data")
                if isinstance(res_data, dict):
                    reply_message = res_data.get("responses")
                else:
                    reply_message = (
                        result.get("data").get("responses") or
                        result.get("reply") or
                        result.get("content") or
                        result.get("response") or
                        result.get("text")
                    )

            if reply_message:
                # Send the reply to guest via WAHA
                waha_phone = format_phone_international_id(phone_number)
                await self.waha_service.send_text_message(
                    phone_number=waha_phone,
                    text=reply_message
                )
                logger.info(f"H2H response forwarded to guest {phone_number} for session {session_id}")
            else:
                logger.warning(f"No reply message found in H2H response for session {session_id}: {result}")

        except Exception as e:
            logger.error(f"Failed to send H2H message or forward response for session {session_id}: {str(e)}")
            # Don't fail - this is a background task

    async def _check_agent_available(self, session_id: UUID) -> bool:
        """
        Check if agent is available for the given session.

        Args:
            session_id: Session ID to check

        Returns:
            True if agent is available, False otherwise
        """
        try:
            agent_available = await self.h2h_service.check_agent_available(session_id)
            logger.info(f"Agent availability check for session {session_id}: {agent_available}")
            return agent_available
        except Exception as e:
            logger.error(f"Failed to check agent availability for session {session_id}: {str(e)}")
            # Return False if check fails - safer to assume agent is not ready
            return False

    async def _create_agent_with_category(self, session_id: UUID, category: str) -> bool:
        """
        Create agent via H2H with specified category.

        Args:
            session_id: Session ID
            category: Agent category

        Returns:
            True if agent created successfully, False otherwise
        """
        try:
            # Create agent via H2H
            agent_result = await self.h2h_service.create_agent(
                session_id=session_id,
                category=category
            )
            logger.info(f"Agent created successfully for session {session_id} with category {category}: {agent_result}")

            # Update session to mark agent as created
            await self.repository.update_session_agent_status(
                session_id=session_id,
                agent_created=True,
                category=category
            )
            await self.db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to create agent for session {session_id}: {str(e)}")
            return False

    async def handle_incoming_message(self, webhook_data: WahaWebhookRequest, background_tasks: BackgroundTasks) -> None:
        """
        Handle incoming message from guest with improved flow logic.

        Flow:
        1. New session: Send welcome message with category options
        2. User responds with 1/2/3: Create agent with category
        3. After agent created: Normal conversation
        4. User sends /end: Terminate session

        Args:
            webhook_data: Webhook data from WAHA
            background_tasks: FastAPI background tasks
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

        logger.info(f"User found for phone number: {phone_number}, user ID: {user.id}")

        # Get active session for user
        session = await self.repository.get_active_session_by_user_id(user.id)

        # Session management logic
        session_needs_creation = False

        if not session:
            # Case 1: No session found - need to create new session
            logger.info(f"No active session found for user: {user.id}, will create new session")
            session_needs_creation = True
        else:
            # Case 2: Session exists - check if it's expired (updated_at > 30 minutes)
            current_time = datetime.now(timezone.utc)
            session_updated_at = session.updated_at

            # Ensure session.updated_at is timezone-aware
            if session_updated_at.tzinfo is None:
                session_updated_at = session_updated_at.replace(tzinfo=timezone.utc)

            time_since_update = current_time - session_updated_at

            if time_since_update > timedelta(minutes=30):
                logger.info(
                    f"Session {session.id} expired (last updated: {time_since_update.total_seconds()/60:.1f} minutes ago), "
                    f"will terminate and create new session"
                )
                # Terminate old session
                await self.repository.terminate_session(session.id)
                await self.db.commit()

                session_needs_creation = True
            else:
                logger.info(f"Using existing active session {session.id} for user {user.id}")

        # Create new session if needed
        if session_needs_creation:
            # Get active checkin room for the user
            checkin_room = await self.repository.get_active_checkin_by_guest_id(user.id)
            if not checkin_room:
                logger.error(f"No active checkin room found for user {user.id}, cannot create session")
                return

            # Create new session
            session = await self.repository.create_session(
                user_id=user.id,
                checkin_room_id=checkin_room.id,
                status=SessionStatus.open,
                mode=SessionMode.agent
            )
            logger.info(f"Created new session {session.id} for user {user.id}")
            await self.db.commit()

            # Send welcome message
            await self._send_welcome_message(
                session_id=session.id,
                phone_number=phone_number,
                user_name=user.name
            )

            # Save the user's message that triggered session creation
            try:
                await self.repository.create_message(
                    session_id=session.id,
                    role=MessageRole.User,
                    text=payload.body or ""
                )
                await self.db.commit()
                logger.info(f"Saved initial message for new session {session.id}")
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Error saving initial message for session {session.id}: {str(e)}")
                raise

            # Return early - don't process the message that triggered session creation
            # Only welcome_text should be sent when session is first created
            logger.info(f"Session {session.id} created and welcome message sent. Waiting for next message.")
            return

        # Check for /end command to terminate session
        user_message = (payload.body or "").strip()
        if user_message == "/end":
            logger.info(f"User {user.id} requested session termination")

            try:
                # Save termination message
                await self.repository.create_message(
                    session_id=session.id,
                    role=MessageRole.User,
                    text=user_message
                )

                # Terminate session
                await self.repository.terminate_session(session.id)
                await self.db.commit()

                # Send goodbye message
                goodbye_text = (
                    "Terima kasih telah menghubungi kami! 👋\n\n"
                    "Sesi percakapan telah berakhir.\n"
                    "Silakan kirim pesan baru jika Anda membutuhkan bantuan lagi.\n\n"
                    "Sampai jumpa! 🏨"
                )

                waha_phone = format_phone_international_id(phone_number)
                await self.waha_service.send_text_message(
                    phone_number=waha_phone,
                    text=goodbye_text
                )
                logger.info(f"Session {session.id} terminated successfully")
                return

            except Exception as e:
                await self.db.rollback()
                logger.error(f"Error terminating session {session.id}: {str(e)}")
                raise

        try:
            # Save incoming message to database with User role
            await self.repository.create_message(
                session_id=session.id,
                role=MessageRole.User,
                text=payload.body or ""
            )
            await self.db.commit()

            # Check if agent has been created for this session
            if not session.agent_created:
                # Agent not created yet - check if user sent category command
                category = self._parse_category_command(user_message)

                if category:
                    logger.info(f"User {user.id} selected category: {category}")

                    # Create agent with selected category
                    agent_created = await self._create_agent_with_category(
                        session_id=session.id,
                        category=category
                    )

                    if agent_created:
                        # Send confirmation message
                        confirmation_text = (
                            f"Terima kasih! 🙏\n\n"
                            f"Anda telah memilih kategori: {category.replace('_', ' ').title()}\n\n"
                            f"Kami siap membantu Anda. Silakan kirim pesan Anda dan "
                            f"tim kami akan segera merespons.\n\n"
                            f"Ketik `/end` kapan saja untuk mengakhiri percakapan."
                        )

                        # Save confirmation message
                        await self.repository.create_message(
                            session_id=session.id,
                            role=MessageRole.System,
                            text=confirmation_text
                        )
                        await self.db.commit()

                        # Send confirmation via WAHA
                        waha_phone = format_phone_international_id(phone_number)
                        await self.waha_service.send_text_message(
                            phone_number=waha_phone,
                            text=confirmation_text
                        )
                        logger.info(f"Agent created and confirmation sent to {phone_number}")
                    else:
                        # Agent creation failed
                        error_text = (
                            "Maaf, terjadi kesalahan saat memproses permintaan Anda. 😔\n\n"
                            "Silakan coba lagi dengan mengirim nomor kategori (1, 2, atau 3)."
                        )

                        waha_phone = format_phone_international_id(phone_number)
                        await self.waha_service.send_text_message(
                            phone_number=waha_phone,
                            text=error_text
                        )
                        logger.error(f"Agent creation failed for session {session.id}")
                else:
                    # Invalid command - ask user to select category again
                    reminder_text = (
                        "Mohon pilih kategori dengan mengirim:\n"
                        "1. General Information\n"
                        "2. Room Service\n"
                        "3. Customer Service\n\n"
                        "Silakan kirim 1, 2, atau 3."
                    )

                    waha_phone = format_phone_international_id(phone_number)
                    await self.waha_service.send_text_message(
                        phone_number=waha_phone,
                        text=reminder_text
                    )
                    logger.info(f"User {user.id} sent invalid command, reminded to select category")
            else:
                # Agent already created - check if agent is actually available
                agent_available = await self._check_agent_available(session.id)

                if not agent_available:
                    # Agent not available yet - send waiting message
                    waiting_text = (
                        "Asisten anda sedang di persiapkan. Silahkan coba beberapa saat lagi."
                    )

                    # Save waiting message
                    await self.repository.create_message(
                        session_id=session.id,
                        role=MessageRole.System,
                        text=waiting_text
                    )
                    await self.db.commit()

                    # Send waiting message via WAHA
                    waha_phone = format_phone_international_id(phone_number)
                    await self.waha_service.send_text_message(
                        phone_number=waha_phone,
                        text=waiting_text
                    )
                    logger.info(f"Agent not available for session {session.id}, sent waiting message to {phone_number}")
                    return

                # Agent is available - normal conversation flow
                # Send typing indicator only
                try:
                    waha_phone = format_phone_international_id(phone_number)
                    await self.waha_service.send_typing_indicator(phone_number=waha_phone)
                except Exception as e:
                    logger.error(f"Failed to send typing indicator to {phone_number}: {str(e)}")
                    # Don't fail the whole operation if sending fails

                await self.db.commit()

                # Send H2H message in background and forward response to guest
                background_tasks.add_task(
                    self._send_h2h_message_background,
                    session.id,
                    user_message,
                    phone_number
                )

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
