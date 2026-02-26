"""Celery tasks — automated turn processing for all active worlds."""

import asyncio

from sqlalchemy import select

from app.database import async_session_factory
from app.models.world import World
from app.services.turn_service import execute_turn
from app.tasks.celery_app import celery_app


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.turn_tasks.process_world_turn")
def process_world_turn(world_id: str) -> dict:
    """Process a single turn for one world."""
    return _run_async(_async_process_world_turn(world_id))


@celery_app.task(name="app.tasks.turn_tasks.process_all_worlds")
def process_all_worlds() -> dict:
    """Process turns for all active, non-maintenance worlds."""
    return _run_async(_async_process_all_worlds())


async def _async_process_world_turn(world_id: str) -> dict:
    async with async_session_factory() as db:
        result = await db.execute(
            select(World).where(
                World.id == world_id,
                World.is_active == True,  # noqa: E712
                World.is_maintenance == False,  # noqa: E712
            )
        )
        world = result.scalar_one_or_none()
        if not world:
            return {"error": f"World {world_id} not found or unavailable"}
        return await execute_turn(world, db)


async def _async_process_all_worlds() -> dict:
    processed = []
    errors = []
    async with async_session_factory() as db:
        result = await db.execute(
            select(World).where(
                World.is_active == True,  # noqa: E712
                World.is_maintenance == False,  # noqa: E712
            )
        )
        worlds = result.scalars().all()

    for world in worlds:
        try:
            summary = _run_async(_async_process_world_turn(str(world.id)))
            processed.append(summary)
        except Exception as e:  # noqa: BLE001
            errors.append({"world_id": str(world.id), "error": str(e)})

    return {"processed": len(processed), "errors": errors}
