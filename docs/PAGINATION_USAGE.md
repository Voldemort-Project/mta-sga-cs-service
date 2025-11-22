# Pagination Utility Usage Guide

Fungsi pagination yang reusable untuk menangani pagination request dari user dengan optimasi database.

## Fitur

- ✅ Pagination (page, per_page)
- ✅ Keyword search dengan ILIKE (case-insensitive)
- ✅ Multi-field ordering dengan format `field:direction;field2:direction2`
- ✅ Metadata pagination lengkap (total, total_pages, has_next, has_prev)
- ✅ Optimized database queries

## Import

```python
from app.core.pagination import PaginationParams, paginate_query
from sqlalchemy import select
from app.models.user import User
```

## Contoh Penggunaan di Router

### 1. Basic Pagination

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.pagination import PaginationParams, paginate_query
from app.models.user import User

router = APIRouter()

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1, description="Current page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    keyword: str = Query(None, description="Search keyword"),
    order: str = Query(None, description="Order string (e.g., 'created_at:desc;name:asc')"),
    db: AsyncSession = Depends(get_db)
):
    # Create pagination params
    params = PaginationParams(
        page=page,
        per_page=per_page,
        keyword=keyword,
        order=order
    )

    # Create base query
    query = select(User)

    # Apply pagination, search, and ordering
    result = await paginate_query(
        db=db,
        query=query,
        params=params,
        model=User,
        search_fields=["name", "email", "mobile_phone"]  # Fields to search in
    )

    return result
```

### 2. Response Format

Response akan memiliki format:

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      ...
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100,
    "total_pages": 10,
    "has_next": true,
    "has_prev": false
  }
}
```

### 3. Format Order String

Order string menggunakan format: `field:direction;field2:direction2`

**Contoh:**
- `"created_at:desc"` - Sort by created_at descending
- `"name:asc;created_at:desc"` - Sort by name ascending, then created_at descending
- `"created_at:desc;name:asc"` - Sort by created_at descending, then name ascending

**Valid directions:**
- `asc` - Ascending
- `desc` - Descending

**Catatan:**
- Jika direction tidak valid, default ke `asc`
- Jika field tidak ada di model, akan di-skip
- Jika tidak ada direction (hanya field), default ke `asc`

### 4. Keyword Search

Keyword search menggunakan ILIKE dengan pattern `%keyword%` (case-insensitive).

**Contoh:**
- `keyword="john"` akan mencari di semua search_fields yang mengandung "john" (case-insensitive)
- Search dilakukan dengan OR condition di semua search_fields

### 5. Contoh Lengkap dengan Filter Tambahan

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.pagination import PaginationParams, paginate_query
from app.models.user import User
from uuid import UUID

router = APIRouter()

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    keyword: str = Query(None),
    order: str = Query(None),
    org_id: UUID = Query(None, description="Filter by organization ID"),
    db: AsyncSession = Depends(get_db)
):
    # Create base query with additional filters
    query = select(User).where(User.deleted_at.is_(None))

    # Add organization filter if provided
    if org_id:
        query = query.where(User.org_id == org_id)

    # Create pagination params
    params = PaginationParams(
        page=page,
        per_page=per_page,
        keyword=keyword,
        order=order
    )

    # Apply pagination
    result = await paginate_query(
        db=db,
        query=query,
        params=params,
        model=User,
        search_fields=["name", "email", "mobile_phone"]
    )

    return result
```

### 6. Menggunakan dengan Schema Response

```python
from pydantic import BaseModel
from app.core.pagination import PaginatedResponse

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True

@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def get_users(...):
    # ... same as above
    return result
```

## Fungsi Utilitas

### `parse_order_string(order_string: str) -> List[tuple[str, str]]`

Parse order string menjadi list of tuples.

```python
from app.core.pagination import parse_order_string

orders = parse_order_string("created_at:desc;name:asc")
# Returns: [('created_at', 'desc'), ('name', 'asc')]
```

### `apply_order_to_query(query, model, order_string)`

Apply ordering ke query tanpa pagination.

```python
from app.core.pagination import apply_order_to_query

query = select(User)
query = apply_order_to_query(query, User, "created_at:desc")
```

### `apply_keyword_search(query, model, keyword, search_fields)`

Apply keyword search ke query tanpa pagination.

```python
from app.core.pagination import apply_keyword_search

query = select(User)
query = apply_keyword_search(query, User, "john", ["name", "email"])
```

## Best Practices

1. **Limit per_page**: Set maximum per_page (e.g., 100) untuk mencegah load berlebihan
2. **Index fields**: Pastikan fields yang digunakan untuk search dan order sudah di-index di database
3. **Search fields**: Pilih fields yang relevan untuk search, jangan terlalu banyak
4. **Default order**: Pertimbangkan untuk set default order jika user tidak provide order string

## Performance Tips

- Fungsi ini sudah optimized dengan:
  - Count query terpisah untuk total
  - Offset/Limit untuk pagination
  - ILIKE untuk case-insensitive search
  - Query yang efisien dengan subquery untuk count

- Untuk performa lebih baik:
  - Gunakan index di database untuk fields yang sering di-search/order
  - Batasi jumlah search_fields
  - Set reasonable limit untuk per_page
