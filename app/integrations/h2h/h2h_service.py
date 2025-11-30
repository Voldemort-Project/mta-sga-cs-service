"""H2H (Host-to-Host) Agent Router Integration Service"""
import httpx
import logging
from uuid import UUID
from typing import Optional

from app.core.config import settings
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode

logger = logging.getLogger(__name__)


class H2HAgentRouterService:
    """Service for interacting with H2H (Host-to-Host) Agent Router API"""

    def __init__(self):
        self.base_url = settings.h2h_agent_router_host
        self.agent_router_path = settings.h2h_agent_router_path
        self.api_key = settings.h2h_agent_router_api_key

    async def create_agent(
        self,
        session_id: UUID,
        category: Optional[str] = None
    ) -> dict:
        """
        Create agent via H2H Agent Router API.

        Args:
            session_id: Session ID (UUID) to use as identifier_id
            category: Agent category (e.g., "room_service", "general_information", "customer_service")

        Returns:
            Response from H2H Agent Router API

        Raises:
            ComposeError: If agent creation fails
        """
        url = f"{self.base_url}{self.agent_router_path}"

        payload = {
            "identifier_id": str(session_id)
        }

        # Add category to payload if provided
        if category:
            payload["category"] = category

        # Prepare headers with API key if configured
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        logger.info(f"Creating agent via H2H Agent Router for session {session_id}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                # Log response for debugging
                logger.debug(f"H2H Agent Router response status: {response.status_code}")
                logger.debug(f"H2H Agent Router response body: {response.text}")

                # Raise exception for HTTP errors
                response.raise_for_status()

                result = response.json()
                logger.info(f"Agent created successfully for session {session_id}")
                return result

        except httpx.HTTPStatusError as e:
            error_msg = f"H2H Agent Router returned {e.response.status_code}"
            if e.response.text:
                error_msg += f": {e.response.text}"

            logger.error(f"HTTP error creating agent for session {session_id}: {error_msg}")
            raise ComposeError(
                error_code=ErrorCode.H2H.AGENT_CREATION_FAILED,
                message=f"Failed to create agent via H2H Agent Router: {error_msg}",
                http_status_code=e.response.status_code,
                original_error=e
            )
        except httpx.RequestError as e:
            error_msg = f"Failed to connect to H2H Agent Router: {str(e)}"
            logger.error(f"Request error creating agent for session {session_id}: {error_msg}")
            raise ComposeError(
                error_code=ErrorCode.H2H.CONNECTION_FAILED,
                message=error_msg,
                http_status_code=500,
                original_error=e
            )
        except Exception as e:
            error_msg = f"Unexpected error creating agent for session {session_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.H2H.UNEXPECTED_ERROR,
                message="An unexpected error occurred while creating agent via H2H Agent Router",
                http_status_code=500,
                original_error=e
            )

    async def send_chat_message(
        self,
        session_id: UUID,
        content: str
    ) -> dict:
        """
        Send chat message via H2H Agent Router API.

        Args:
            session_id: Session ID (UUID) to identify the conversation
            content: Message content to send

        Returns:
            Response from H2H Agent Router API

        Raises:
            ComposeError: If sending message fails
        """
        url = f"{self.base_url}/v2/chats"

        payload = {
            "session_id": str(session_id),
            "content": content
        }

        # Prepare headers with API key if configured
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        logger.info(f"Sending chat message via H2H Agent Router for session {session_id}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                # Log response for debugging
                logger.debug(f"H2H Agent Router response status: {response.status_code}")
                logger.debug(f"H2H Agent Router response body: {response.text}")

                # Raise exception for HTTP errors
                response.raise_for_status()

                result = response.json()
                logger.info(f"Chat message sent successfully for session {session_id}")
                return result

        except httpx.HTTPStatusError as e:
            error_msg = f"H2H Agent Router returned {e.response.status_code}"
            if e.response.text:
                error_msg += f": {e.response.text}"

            logger.error(f"HTTP error sending chat message for session {session_id}: {error_msg}")
            raise ComposeError(
                error_code=ErrorCode.H2H.AGENT_CREATION_FAILED,
                message=f"Failed to send chat message via H2H Agent Router: {error_msg}",
                http_status_code=e.response.status_code,
                original_error=e
            )
        except httpx.RequestError as e:
            error_msg = f"Failed to connect to H2H Agent Router: {str(e)}"
            logger.error(f"Request error sending chat message for session {session_id}: {error_msg}")
            raise ComposeError(
                error_code=ErrorCode.H2H.CONNECTION_FAILED,
                message=error_msg,
                http_status_code=500,
                original_error=e
            )
        except Exception as e:
            error_msg = f"Unexpected error sending chat message for session {session_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ComposeError(
                error_code=ErrorCode.H2H.UNEXPECTED_ERROR,
                message="An unexpected error occurred while sending chat message via H2H Agent Router",
                http_status_code=500,
                original_error=e
            )
