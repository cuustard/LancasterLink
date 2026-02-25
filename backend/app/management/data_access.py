"""
LancasterLink – Database Access Layer.

Provides:
    * SQLAlchemy engine creation and session management.
    * A ``SessionManager`` singleton used by the FastAPI lifespan handler.
    * A ``get_db`` dependency for injecting DB sessions into route handlers.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ── Declarative Base ─────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ── Session Manager ──────────────────────────────────────────────────────
class SessionManager:
    """Thin wrapper around SQLAlchemy engine + sessionmaker.

    Usage (inside FastAPI lifespan)::

        sessionmanager.init(database_url)
        ...
        sessionmanager.close()
    """

    def __init__(self) -> None:
        self._engine = None
        self._session_factory = None

    def init(self, database_url: str, **engine_kwargs) -> None:
        """Create the engine and session factory.

        Args:
            database_url: SQLAlchemy database URL.
            **engine_kwargs: Extra arguments forwarded to ``create_engine``
                (e.g. ``pool_size``, ``echo``).
        """
        self._engine = create_engine(
            database_url,
            pool_pre_ping=True,
            **engine_kwargs,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def close(self) -> None:
        """Dispose of the engine and release all pooled connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def session(self) -> Session:
        """Create a new session.  Caller is responsible for closing it."""
        if self._session_factory is None:
            raise RuntimeError(
                "SessionManager is not initialised – call init() first."
            )
        return self._session_factory()

    @property
    def engine(self):
        return self._engine


# Module-level singleton used across the application.
sessionmanager = SessionManager()

# Convenience alias so main.py can do: from app.management.data_access import engine
engine = None  # Access via sessionmanager.engine after init()


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session.

    Example::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = sessionmanager.session()
    try:
        yield db
    finally:
        db.close()
