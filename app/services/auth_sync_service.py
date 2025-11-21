"""Service for syncing Keycloak token data to database"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.organization import Organization
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import TokenData


class AuthSyncService:
    """Service to sync authentication data from Keycloak token to database"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_token_data(self, token_data: TokenData) -> tuple[Organization, User]:
        """
        Sync organization and user data from token to database

        Args:
            token_data: Decoded token data from Keycloak

        Returns:
            tuple: (organization, user) - The synced/created database records
        """
        print(f"[AuthSync] Starting sync for user: {token_data.user.user_id}, org: {token_data.organization_id}")

        # Sync organization first (user depends on org)
        print(f"[AuthSync] Syncing organization: {token_data.organization_name} ({token_data.organization_id})")
        organization = await self.sync_organization(
            org_id=token_data.organization_id,
            org_name=token_data.organization_name
        )
        print(f"[AuthSync] Organization synced successfully: {organization.name}")

        # Sync user
        print(f"[AuthSync] Syncing user: {token_data.user.name} ({token_data.user.user_id})")
        user = await self.sync_user(
            user_id=token_data.user.user_id,
            org_id=token_data.organization_id,
            name=token_data.user.name,
            email=token_data.user.email,
            username=token_data.user.username
        )
        print(f"[AuthSync] User synced successfully: {user.name}")

        return organization, user

    async def sync_organization(self, org_id: str, org_name: str) -> Organization:
        """
        Create or update organization in database

        Args:
            org_id: Organization UUID from Keycloak
            org_name: Organization name from Keycloak

        Returns:
            Organization: The organization record
        """
        # Convert string UUID to uuid.UUID
        org_uuid = uuid.UUID(org_id)

        # Check if organization exists
        stmt = select(Organization).where(Organization.id == org_uuid)
        result = await self.db.execute(stmt)
        organization = result.scalar_one_or_none()

        if organization:
            # Update organization name if changed
            print(f"[AuthSync] Organization exists, checking for updates...")
            if organization.name != org_name:
                print(f"[AuthSync] Updating organization name: {organization.name} → {org_name}")
                organization.name = org_name
                await self.db.commit()
                await self.db.refresh(organization)
            else:
                print(f"[AuthSync] Organization up to date")
        else:
            # Create new organization
            print(f"[AuthSync] Creating new organization: {org_name} ({org_uuid})")
            organization = Organization(
                id=org_uuid,
                name=org_name,
                address=None  # Will be updated later if needed
            )
            self.db.add(organization)
            await self.db.commit()
            await self.db.refresh(organization)
            print(f"[AuthSync] Organization created successfully")

        return organization

    async def sync_user(
        self,
        user_id: str,
        org_id: str,
        name: str,
        email: str,
        username: str
    ) -> User:
        """
        Create or update user in database

        Args:
            user_id: User UUID from Keycloak (sub claim)
            org_id: Organization UUID
            name: User full name
            email: User email
            username: Username

        Returns:
            User: The user record
        """
        # Convert string UUIDs to uuid.UUID
        user_uuid = uuid.UUID(user_id)
        org_uuid = uuid.UUID(org_id)

        # Check if user exists
        stmt = select(User).where(User.id == user_uuid)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update user data if changed
            print(f"[AuthSync] User exists, checking for updates...")
            updated = False
            if user.name != name:
                print(f"[AuthSync] Updating user name: {user.name} → {name}")
                user.name = name
                updated = True
            if user.email != email:
                print(f"[AuthSync] Updating user email: {user.email} → {email}")
                user.email = email
                updated = True
            if user.org_id != org_uuid:
                print(f"[AuthSync] Updating user org_id: {user.org_id} → {org_uuid}")
                user.org_id = org_uuid
                updated = True

            if updated:
                await self.db.commit()
                await self.db.refresh(user)
                print(f"[AuthSync] User updated successfully")
            else:
                print(f"[AuthSync] User up to date")
        else:
            # Get or create default role for Keycloak users
            print(f"[AuthSync] User not found, creating new user...")
            print(f"[AuthSync] Getting or creating default role...")
            default_role = await self._get_or_create_default_role()
            print(f"[AuthSync] Default role: {default_role.name} ({default_role.id})")

            # Create new user
            print(f"[AuthSync] Creating user with data:")
            print(f"  - id: {user_uuid}")
            print(f"  - org_id: {org_uuid}")
            print(f"  - role_id: {default_role.id}")
            print(f"  - name: {name}")
            print(f"  - email: {email}")

            user = User(
                id=user_uuid,
                org_id=org_uuid,
                role_id=default_role.id,
                name=name,
                email=email,
                phone=None,  # Not available from Keycloak token
                id_card_number=None,  # Not available from Keycloak token
                division_id=None  # Can be assigned later
            )
            self.db.add(user)
            print(f"[AuthSync] User added to session, committing...")
            await self.db.commit()
            print(f"[AuthSync] Commit successful, refreshing...")
            await self.db.refresh(user)
            print(f"[AuthSync] User created successfully: {user.id}")

        return user

    async def _get_or_create_default_role(self) -> Role:
        """
        Get or create default role for Keycloak authenticated users

        Returns:
            Role: The default role
        """
        # Look for existing "Keycloak User" role
        stmt = select(Role).where(Role.name == "Keycloak User")
        result = await self.db.execute(stmt)
        role = result.scalar_one_or_none()

        if not role:
            # Create default role
            print(f"[AuthSync] Default role not found, creating...")
            role = Role(
                name="Keycloak User"
            )
            self.db.add(role)
            await self.db.commit()
            await self.db.refresh(role)
            print(f"[AuthSync] Default role created: {role.name} ({role.id})")
        else:
            print(f"[AuthSync] Default role found: {role.name} ({role.id})")

        return role


async def sync_auth_data(db: AsyncSession, token_data: TokenData) -> tuple[Organization, User]:
    """
    Helper function to sync authentication data

    Usage:
        org, user = await sync_auth_data(db, token_data)

    Args:
        db: Database session
        token_data: Decoded token data

    Returns:
        tuple: (organization, user)
    """
    service = AuthSyncService(db)
    return await service.sync_token_data(token_data)
