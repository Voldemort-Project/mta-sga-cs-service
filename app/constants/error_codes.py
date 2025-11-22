"""Error code constants for the application

This module contains all error codes used throughout the application.
Error codes follow the format: {http_prefix}_{status_code}_{category}_{specific_code}

Format:
- http_prefix: 4 for 4xx errors, 5 for 5xx errors
- status_code: HTTP status code (e.g., 000 for generic, 404 for not found)
- category: Module/feature category (e.g., 000 for general, 001 for guest)
- specific_code: Specific error within the category

Example:
- 4_000_000_0000001: Generic not found error
- 4_000_001_0000001: Guest-related not found error
- 5_000_001_0000001: Guest-related internal server error
"""


class ErrorCode:
    """Error code constants organized by category"""

    # ============================================
    # General Errors (000)
    # ============================================
    class General:
        """General application errors"""
        # Validation errors
        VALIDATION_ERROR = "4_000_000_0000000"

        # Not Found (404)
        NOT_FOUND = "4_000_000_0000001"

        # Bad Request (400)
        BAD_REQUEST = "4_000_000_0000002"

        # Internal Server Error (500)
        INTERNAL_SERVER_ERROR = "5_000_000_0000000"
        UNEXPECTED_ERROR = "5_000_000_0000001"

    # ============================================
    # Guest Service Errors (001)
    # ============================================
    class Guest:
        """Guest service related errors"""
        # Not Found (404)
        ROOM_NOT_FOUND = "4_000_001_0000001"

        # Bad Request (400)
        ROOM_ALREADY_BOOKED = "4_000_001_0000002"

        # Internal Server Error (500)
        GUEST_ROLE_NOT_FOUND = "5_000_001_0000001"
        REGISTRATION_FAILED = "5_000_001_0000002"

    # ============================================
    # Add more categories below as needed
    # ============================================
    # class Room:
    #     """Room service related errors"""
    #     NOT_FOUND = "4_000_002_0000001"
    #     ...
    #
    # class User:
    #     """User service related errors"""
    #     NOT_FOUND = "4_000_003_0000001"
    #     ...
