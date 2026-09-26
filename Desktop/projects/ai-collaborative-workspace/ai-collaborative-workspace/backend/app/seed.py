import asyncio
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.workspace import User, Workspace, WorkspaceMember, Document, RoleEnum

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check if seed user exists
        demo_user = User(
            email="demo@workspace.ai",
            hashed_password=get_password_hash("password123"),
            full_name="Demo Developer"
        )
        session.add(demo_user)
        await session.flush()

        # Seed Workspace
        workspace = Workspace(
            name="Engineering Alpha Workspace",
            description="Core engineering collaborative space",
            owner_id=demo_user.id
        )
        session.add(workspace)
        await session.flush()

        # Seed Member
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=demo_user.id,
            role=RoleEnum.ADMIN
        )
        session.add(member)

        # Seed Sample Document
        doc = Document(
            workspace_id=workspace.id,
            title="System Architecture Guidelines",
            content="# Welcome to AI Collaborative Workspace\nThis document is synced real-time.",
            created_by=demo_user.id
        )
        session.add(doc)

        await session.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())