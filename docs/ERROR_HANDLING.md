# Error Handling Documentation

## Overview

Sistem error handling yang terstruktur dengan format response standar untuk semua error yang terjadi di aplikasi.

## Format Error Response

Semua error response mengikuti format berikut:

```json
{
  "code": "4_000_000_0000001",
  "message": "Room not found",
  "data": {
    "error_type": "NotFoundError",
    "error_message": "Room 101 not found",
    "stack_trace": ["..."]
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### Field Description

- **code**: Custom error code sesuai dengan error yang terjadi (e.g: `4_000_000_0000001`)
- **message**: Pesan error yang akan ditampilkan di user interface (web, mobile, etc)
- **data**: Error stack atau data tambahan dari sistem
  - **Note**: Field `data` hanya ditampilkan di environment non-production
  - Di production, field `data` akan di-exclude dari response
- **timestamp**: Waktu ketika error terjadi

## Error Code Constants

**⚠️ IMPORTANT: Jangan hardcode error codes!**

Semua error codes dikelola di `app/constants/error_codes.py` untuk memudahkan maintenance dan konsistensi.

### Struktur Error Code

Error codes diorganisir berdasarkan kategori/module:

```python
from app.constants.error_codes import ErrorCode

# General errors
ErrorCode.General.VALIDATION_ERROR
ErrorCode.General.NOT_FOUND
ErrorCode.General.BAD_REQUEST
ErrorCode.General.INTERNAL_SERVER_ERROR

# Guest service errors
ErrorCode.Guest.ROOM_NOT_FOUND
ErrorCode.Guest.ROOM_ALREADY_BOOKED
ErrorCode.Guest.GUEST_ROLE_NOT_FOUND
ErrorCode.Guest.REGISTRATION_FAILED
```

### Menambah Error Code Baru

1. Buka `app/constants/error_codes.py`
2. Tambahkan error code di kategori yang sesuai (atau buat kategori baru)
3. Gunakan format: `{http_prefix}_{status_code}_{category}_{specific_code}`

Contoh:
```python
class Guest:
    """Guest service related errors"""
    # Not Found (404)
    ROOM_NOT_FOUND = "4_000_001_0000001"

    # Bad Request (400)
    ROOM_ALREADY_BOOKED = "4_000_001_0000002"
```

## ComposeError Exception

Custom exception yang digunakan di level service untuk raise error dengan format standar.

### Usage

**✅ BENAR - Menggunakan ErrorCode constants:**

```python
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from fastapi import status

# Basic usage
raise ComposeError(
    error_code=ErrorCode.Guest.ROOM_NOT_FOUND,
    message="Room not found",
    http_status_code=status.HTTP_404_NOT_FOUND
)

# With original error (for stack trace in non-production)
try:
    # some operation
    pass
except Exception as e:
    raise ComposeError(
        error_code=ErrorCode.Guest.REGISTRATION_FAILED,
        message="Failed to process request",
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        original_error=e
    )
```

**❌ SALAH - Hardcode error code:**

```python
# JANGAN LAKUKAN INI!
raise ComposeError(
    error_code="4_000_000_0000001",  # Hardcoded - tidak maintainable!
    message="Room not found",
    http_status_code=status.HTTP_404_NOT_FOUND
)
```

### Parameters

- **error_code** (str, required): Custom error code dari `ErrorCode` constants
- **message** (str, required): User-friendly error message
- **http_status_code** (int, optional): HTTP status code (default: 500)
- **original_error** (Any, optional): Original exception atau error data untuk stack trace

## Error Code Convention

Format error code: `{http_status_prefix}_{status_code}_{category}_{specific_code}`

Contoh:
- `4_000_000_0000001` - Not Found (404)
- `4_000_000_0000002` - Bad Request (400)
- `5_000_000_0000001` - Internal Server Error (500)

## Environment Configuration

Error stack trace hanya ditampilkan di environment non-production. Konfigurasi berdasarkan `ENV` di `app/core/config.py`:

- **Production**: `env = "production"` - Stack trace tidak ditampilkan
- **Development/Staging**: `env != "production"` - Stack trace ditampilkan

## Exception Handlers

Sistem menggunakan exception handlers di FastAPI untuk menangkap berbagai jenis error:

1. **ComposeError**: Custom error dari service layer
2. **HTTPException**: Standard FastAPI HTTP exceptions
3. **RequestValidationError**: Pydantic validation errors
4. **Exception**: Fallback untuk unhandled exceptions

## Best Practices

1. **Service Layer Only**: Gunakan `ComposeError` hanya di level service, bukan di router
2. **Error Code Constants**: **JANGAN hardcode error codes!** Selalu gunakan `ErrorCode` constants dari `app/constants/error_codes.py`
3. **Error Codes**: Gunakan error code yang konsisten dan terstruktur sesuai format
4. **User-Friendly Messages**: Pastikan message mudah dipahami oleh end user
5. **Original Error**: Selalu pass `original_error` untuk debugging di development
6. **HTTP Status Codes**: Gunakan HTTP status code yang sesuai dengan jenis error
7. **Konsistensi**: Gunakan error code yang sudah ada jika sesuai, jangan membuat duplikat

## Examples

### Example 1: Not Found Error

```python
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from fastapi import status

# In service
room = await self.repository.get_room_by_number(room_number)
if not room:
    raise ComposeError(
        error_code=ErrorCode.Guest.ROOM_NOT_FOUND,
        message=f"Room {room_number} not found",
        http_status_code=status.HTTP_404_NOT_FOUND
    )
```

### Example 2: Validation Error

```python
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from fastapi import status

# In service
if room.is_booked:
    raise ComposeError(
        error_code=ErrorCode.Guest.ROOM_ALREADY_BOOKED,
        message=f"Room {room_number} is already booked",
        http_status_code=status.HTTP_400_BAD_REQUEST
    )
```

### Example 3: Internal Server Error with Stack Trace

```python
from app.core.exceptions import ComposeError
from app.constants.error_codes import ErrorCode
from fastapi import status

# In service
try:
    result = await some_operation()
except Exception as e:
    raise ComposeError(
        error_code=ErrorCode.Guest.REGISTRATION_FAILED,
        message="Failed to process request. Please try again.",
        http_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        original_error=e
    )
```

## Response Examples

### Development Environment

```json
{
  "code": "4_000_000_0000001",
  "message": "Room 101 not found",
  "data": {
    "error_type": "ComposeError",
    "error_message": "Room 101 not found",
    "stack_trace": [
      "Traceback (most recent call last):",
      "  File \"app/services/guest_service.py\", line 58, in register_guest",
      "    raise ComposeError(...)",
      "ComposeError: Room 101 not found"
    ]
  },
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

### Production Environment

```json
{
  "code": "4_000_000_0000001",
  "message": "Room 101 not found",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```
