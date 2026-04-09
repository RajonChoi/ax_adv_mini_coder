import os
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    user_id = Column(String(255), primary_key=True)
    attributes = Column(JSONB, default=dict, nullable=False)

class MemoryManager:
    def __init__(self, db_url=None):
        if db_url is None:
            # Fallback to default DB url if not provided in env
            db_url = os.getenv("DATABASE_URL", "postgresql://jrue_coder:jrue_coder@localhost:5432/jrue_coder")

        # Replace postgres:// with postgresql:// for SQLAlchemy
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def update_user_profile(self, user_id: str, new_attributes: dict):
        with self.SessionLocal() as session:
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            if not profile:
                profile = UserProfile(user_id=user_id, attributes=new_attributes)
                session.add(profile)
            else:
                # Merge new attributes
                updated_attrs = dict(profile.attributes)
                updated_attrs.update(new_attributes)

                # Assign a new dict so SQLAlchemy detects the change to JSONB
                profile.attributes = updated_attrs
            session.commit()

    def get_user_profile(self, user_id: str) -> dict:
        with self.SessionLocal() as session:
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            if profile:
                return profile.attributes
            return {}
    def delete_user_attribute(self, user_id: str, attribute_name: str):
        with self.SessionLocal() as session:
            profile = session.query(UserProfile).filter_by(user_id=user_id).first()
            if profile and attribute_name in profile.attributes:
                updated_attrs = dict(profile.attributes)
                del updated_attrs[attribute_name]
                profile.attributes = updated_attrs
                session.commit()

# Define a native tool that the AI Agent can invoke
def save_user_characteristic(trait_name: str, trait_value: str) -> str:
    """
    Save a user characteristic, trait, or preference to long-term memory.
    Use this tool whenever the user mentions personal information
    (e.g., where they live, what languages they like, hobbies, etc.).
    """
    manager = MemoryManager()
    manager.update_user_profile(
        user_id="default_user",
        new_attributes={trait_name: trait_value}
    )
    return f"Successfully saved {trait_name} = {trait_value} to user profile."

def delete_user_characteristic(trait_name: str) -> str:
    """
    Delete a user characteristic, trait, or preference from long-term memory.
    Use this tool whenever the user wants to remove personal information
    (e.g., they no longer want to share their location or hobbies).
    """
    manager = MemoryManager()
    manager.update_user_profile(
        user_id="default_user",
        new_attributes={trait_name: None}  # Setting to None will remove the key
    )
    return f"Successfully deleted {trait_name} from user profile."
