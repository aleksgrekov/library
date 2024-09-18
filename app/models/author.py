from typing import Any

from sqlalchemy import Text
from sqlalchemy.orm import relationship, backref, Mapped, mapped_column

from module_21_orm_2.homework.app.models.init import Base


class Author(Base):
    __tablename__ = 'authors'

    author_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    surname: Mapped[str] = mapped_column(Text)

    books = relationship('Book', backref=backref('author', cascade='all', lazy='joined'))

    def __init__(self, name, surname, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.surname = surname

    def __repr__(self):
        return ("Author("
                f"\n\tauthor_id = {self.author_id}"
                f"\n\tname = {self.name}"
                f"\n\tsurname = {self.surname}"
                f"\n\tbooks = {self.books}"
                "\n)")
