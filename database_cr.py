import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Boolean, text
from sqlalchemy.orm import declarative_base, Session
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///campus_crowd.db")

# Render gives PostgreSQL URLs starting with "postgres://" but SQLAlchemy
# requires "postgresql://". This fixes that automatically.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # test connection before using it, handles dropped connections
    pool_recycle=300,     # recycle connections every 5 minutes
)

Base = declarative_base()
class Checkin(Base):
    __tablename__ = "checkins"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    spot      = Column(String,  nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)    

class ManualRating(Base):
    __tablename__ = "manual_ratings"

    id        = Column(Integer,  primary_key=True, autoincrement=True)
    spot      = Column(String,   nullable=False)
    score     = Column(Float,    nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class PollState(Base):
    __tablename__ = "poll_state"

    id            = Column(Integer,  primary_key=True, default=1)
    date          = Column(String,   nullable=True)
    last_reset    = Column(String,   nullable=True)
    lunch         = Column(Boolean,  nullable=True)
    dinner        = Column(Boolean,  nullable=True)
    lunch_good    = Column(Integer,  default=0)
    lunch_bad     = Column(Integer,  default=0)
    dinner_good   = Column(Integer,  default=0)
    dinner_bad    = Column(Integer,  default=0)

class PollVote(Base):
    __tablename__ = "poll_votes"

    id        = Column(Integer,  primary_key=True, autoincrement=True)
    meal      = Column(String,   nullable=False)
    voter_ip  = Column(String,   nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

class ActionLog(Base):
    __tablename__ = "action_log"
    id        = Column(Integer,  primary_key=True, autoincrement=True)
    action    = Column(String,   nullable=False)  # "checkin" or "rate"
    actor_ip  = Column(String,   nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

def init_db():
    """Create all tables if they don't exist. Safe to call multiple times."""
    Base.metadata.create_all(engine)

    # Make sure the single poll row exists
    with Session(engine) as session:
        if not session.get(PollState, 1):
            session.add(PollState(id=1))
            session.commit()

def get_poll():
    """Return the single poll row, always."""
    with Session(engine) as session:
        return session.get(PollState, 1)

def save_poll(updates: dict):
    with Session(engine) as session:
        poll = session.get(PollState, 1)
        if poll is None:
            poll = PollState(id=1)
            session.add(poll)
        for key, value in updates.items():
            setattr(poll, key, value)
        session.commit()

def add_checkin(spot):
    with Session(engine) as session:
        session.add(Checkin(spot=spot, timestamp=datetime.utcnow()))
        session.commit()

def add_rating(spot, score):
    with Session(engine) as session:
        session.add(ManualRating(spot=spot, score=score, timestamp=datetime.utcnow()))
        session.commit()

def get_active_checkins(spot, cutoff):
    """Return checkins for a spot after the cutoff datetime."""
    with Session(engine) as session:
        return session.query(Checkin)\
            .filter(Checkin.spot == spot, Checkin.timestamp > cutoff)\
            .all()

def get_all_active_checkins(cutoff):
    """Return all checkins across all spots after the cutoff datetime."""
    with Session(engine) as session:
        return session.query(Checkin)\
            .filter(Checkin.timestamp > cutoff)\
            .all()

def get_active_ratings(spot, cutoff):
    """Return manual ratings for a spot after the cutoff datetime."""
    with Session(engine) as session:
        return session.query(ManualRating)\
            .filter(ManualRating.spot == spot, ManualRating.timestamp > cutoff)\
            .all()

def get_recent_poll_vote(meal, voter_ip, seconds=30):
    """Returns True if this IP voted for this meal in the last 30 seconds."""
    cutoff = datetime.utcnow() - timedelta(seconds=seconds)
    with Session(engine) as session:
        result = session.query(PollVote).filter(
            PollVote.meal == meal,
            PollVote.voter_ip == voter_ip,
            PollVote.timestamp > cutoff
        ).first()
        return result is not None

def add_poll_vote(meal, voter_ip):
    with Session(engine) as session:
        session.add(PollVote(meal=meal, voter_ip=voter_ip))
        session.commit()

def add_action_log(action, actor_ip):
    with Session(engine) as session:
        session.add(ActionLog(
            action=action,
            actor_ip=actor_ip,
            timestamp=datetime.utcnow()
        ))
        session.commit()

def get_recent_action(action, actor_ip, minutes=5):
    """Returns True if this IP performed this action in the last N minutes."""
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    with Session(engine) as session:
        result = session.query(ActionLog).filter(
            ActionLog.action == action,
            ActionLog.actor_ip == actor_ip,
            ActionLog.timestamp > cutoff
        ).first()
        return result is not None
