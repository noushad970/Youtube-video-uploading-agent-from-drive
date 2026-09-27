import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base, AgentSettings, User, GoogleCredential, DriveFolder, Video, Upload
from app.database.repository import Repository

# In-memory SQLite for high-speed tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Create default settings
    default_settings = AgentSettings(
        enabled=False,
        interval_minutes=360,
        privacy_status="private",
        category_id="20",
        generate_title=True,
        generate_description=True,
        generate_tags=True,
        ollama_model="qwen3:8b",
        max_retries=3,
        delete_after_upload=True,
        fallback_if_ai_unavailable=True,
    )
    session.add(default_settings)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repo(db_session):
    return Repository(db_session)
