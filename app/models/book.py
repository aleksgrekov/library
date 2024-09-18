from datetime import date
from typing import Optional, Tuple, Union, List, Dict, Any

from sqlalchemy import Text, ForeignKey, Index, func, select, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship

from module_21_orm_2.homework.app.models.init import Base, session
from module_21_orm_2.homework.app.models.receiving_books import ReceivingBooks
from module_21_orm_2.homework.app.models.student import Student


class Book(Base):
    __tablename__ = 'books'

    book_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column('name', Text)
    count: Mapped[int] = mapped_column(default=1)
    release_date: Mapped[date]
    author_id: Mapped[int] = mapped_column(ForeignKey('authors.author_id'))

    students: Mapped['ReceivingBooks'] = relationship(
        back_populates='book',
        cascade='all',
        lazy='subquery'
    )

    __table_args__ = (
        Index('ix_books_author_id', 'author_id'),
    )

    def __init__(self, title, count, release_date, **kw: Any):
        super().__init__(**kw)
        self.name = title
        self.count = count
        self.release_date = release_date

    def __repr__(self):
        return ("Book("
                f"\n\tbook_id = {self.book_id}"
                f"\n\tname = {self.name}"
                f"\n\tcount = {self.count}"
                f"\n\trelease_date = {self.release_date}"
                f"\n\tauthor_id = {self.author_id}"
                "\n)")

    @classmethod
    def all_books(cls) -> Optional[List['Book']]:
        return session.scalars(select(Book)).all()

    @classmethod
    def book_by_name(cls, title: str) -> List['Book']:
        query = select(Book).where(Book.name.like(f'%{title}%'))
        return session.scalars(query).all()

    @classmethod
    def most_popular_book(cls) -> Tuple['Book', int]:
        query = select(
            Book,
            func.count(ReceivingBooks.receipt_id).label('row_count')
        ).join(
            Student, ReceivingBooks.student
        ).join(
            Book, ReceivingBooks.book
        ).group_by(
            ReceivingBooks.book_id
        ).having(
            Student.average_score > 4
        ).order_by(
            desc('row_count'),
            desc(Book.count)
        )
        # При выполнении запроса получаю следующее сообщение:
        # SAWarning: Multiple rows returned with uselist=False for eagerly-loaded attribute 'Book.students'
        #   return session.execute(query).first()
        return session.execute(query).first()

    @classmethod
    def recommendations_for_student(cls, student_id: int) -> Union[List['Book'], Tuple[str, int]]:
        student: Optional['Student'] = Student.student_by_id(student_id)

        if not student:
            return 'There is no student with this ID', 400

        query = select(Book).where(
            Book.author_id.in_(student.books_author),
            Book.name.notin_(student.books_titles)
        )
        books = session.scalars(query).all()

        if not books:
            return 'There are no recommendations for this student yet', 404

        return books

    @classmethod
    def sum_of_books_by_author_id(cls, author_id: int) -> int:
        query = select(func.sum(Book.count)).where(Book.author_id == author_id)
        return session.scalar(query)

    def to_json(self) -> Dict[str, Any]:
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
