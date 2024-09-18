from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine('sqlite:///library.db', echo=False)
Session = sessionmaker(bind=engine)
session = Session()


class Base(DeclarativeBase):
    pass
