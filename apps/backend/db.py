import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import settings

Base = declarative_base()


class JobStatus(str, Enum):
    QUEUED = "queued"
    REJECTED = "rejected"
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"


class JobScope(str, Enum):
    READ_ONLY = "read-only"
    SANDBOX = "sandbox"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: f"job_{uuid.uuid4().hex}")
    target_url = Column(String, nullable=False)
    scope = Column(SAEnum(JobScope), nullable=False)
    test_profile = Column(String, nullable=False)
    owner_id = Column(String, nullable=False)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.QUEUED)
    preflight_allowed = Column(Boolean, nullable=True)
    preflight_robots = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    consent_logs = relationship("ConsentLog", back_populates="job")


class ConsentLog(Base):
    __tablename__ = "consent_logs"

    id = Column(
        String,
        primary_key=True,
        default=lambda: f"consent_{uuid.uuid4().hex}",
    )
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    owner_id = Column(String, nullable=False)
    consent_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    note = Column(Text, nullable=True)

    job = relationship("Job", back_populates="consent_logs")


engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

