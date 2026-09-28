from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite:///./fitbuddy.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)

    age = Column(String)

    gender = Column(String)

    height = Column(String)

    weight = Column(String)

    goal = Column(String)

    fitness_level = Column(String)

    equipment = Column(String)

    workout_plan = Column(Text)

    nutrition_tips = Column(Text)

    feedback = Column(Text)


Base.metadata.create_all(bind=engine)