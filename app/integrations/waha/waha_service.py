"""WAHA (WhatsApp HTTP API) Integration Service"""
import httpx
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class WahaService:
    """Service for interacting with WAHA API"""

    def __init__(self):
        self.base_url = settings.waha_host
        self.api_path = settings.waha_api_path
        self.session = settings.waha_session
        self.api_key = settings.waha_api_key

    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to WhatsApp chatId format.

        Args:
            phone: Phone number (e.g., "081234567890" or "+6281234567890")

        Returns:
            Formatted chatId (e.g., "6281234567890@c.us")
        """
        # Remove any non-digit characters
        phone_digits = ''.join(filter(str.isdigit, phone))

        # Add 62 prefix if not present
        if not phone_digits.startswith('62'):
            # Remove leading 0 if present
            if phone_digits.startswith('0'):
                phone_digits = '62' + phone_digits[1:]
            else:
                phone_digits = '62' + phone_digits

        return phone_digits

    async def send_text_message(
        self,
        phone_number: str,
        text: str,
        reply_to: Optional[str] = None,
        link_preview: bool = True,
        link_preview_high_quality: bool = False
    ) -> dict:
        """
        Send text message via WAHA API.

        Args:
            phone_number: Recipient's phone number
            text: Message text to send
            reply_to: Optional message ID to reply to
            link_preview: Enable link preview
            link_preview_high_quality: Enable high quality link preview

        Returns:
            Response from WAHA API

        Raises:
            Exception: If message sending fails
        """
        chat_id = self._format_phone_number(phone_number)
        url = f"{self.base_url}{self.api_path}"

        payload = {
            "chatId": chat_id,
            "reply_to": reply_to,
            "text": text,
            "linkPreview": link_preview,
            "linkPreviewHighQuality": link_preview_high_quality,
            "session": self.session
        }

        # Prepare headers with API key if configured
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        logger.info(f"Sending message to {chat_id}: {text[:50]}...")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                logger.info(f"Message sent successfully to {chat_id}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending message to {chat_id}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to send message: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error sending message to {chat_id}: {str(e)}")
            raise Exception(f"Failed to connect to WAHA service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending message to {chat_id}: {str(e)}")
            raise

    async def send_welcome_message(self, phone_number: str, guest_name: str, room_number: str) -> dict:
        """
        Send welcome message to new guest.

        Args:
            phone_number: Guest's phone number
            guest_name: Guest's full name
            room_number: Room number

        Returns:
            Response from WAHA API
        """
        welcome_text = (
            f"Halo {guest_name}! 👋\n\n"
            f"Selamat datang di hotel kami. Anda telah berhasil check-in di kamar {room_number}.\n\n"
            f"Jika Anda membutuhkan bantuan atau memiliki pertanyaan, "
            f"silakan balas pesan ini dan kami akan segera membantu Anda.\n\n"
            f"Terima kasih telah memilih hotel kami. Semoga Anda menikmati masa menginap Anda! 🏨"
        )

        return await self.send_text_message(phone_number, welcome_text)

    async def send_auto_reply(self, phone_number: str) -> dict:
        """
        Send automatic reply to guest message.

        Args:
            phone_number: Guest's phone number

        Returns:
            Response from WAHA API
        """
        auto_reply_text = (
            "Terima kasih atas pesan Anda. 🙏\n\n"
            "Tim kami akan segera merespons pertanyaan Anda. "
            "Mohon menunggu sebentar.\n\n"
            "Waktu respon normal: 5-10 menit"
        )

        return await self.send_text_message(phone_number, auto_reply_text)

    async def send_typing_indicator(self, phone_number: str) -> dict:
        """
        Send typing indicator to guest.

        Args:
            phone_number: Guest's phone number

        Returns:
            Response from WAHA API
        """
        chat_id = self._format_phone_number(phone_number)
        url = f"{self.base_url}/api/startTyping"
        payload = {
            "chatId": chat_id,
            "session": self.session
        }
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        logger.info(f"Sending typing indicator to {chat_id}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                logger.info(f"Message sent indicator typing successfully to {chat_id}")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error sending message to {chat_id}: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to send message: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error sending message to {chat_id}: {str(e)}")
            raise Exception(f"Failed to connect to WAHA service: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error sending message to {chat_id}: {str(e)}")
            raise
