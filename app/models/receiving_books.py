from datetime import datetime
from typing import Any, List, Tuple, Dict, Optional

from sqlalchemy import ForeignKey, case, func, extract, select, desc, update, insert
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, Mapped, mapped_column

from module_21_orm_2.homework.app.models.init import Base, session
from module_21_orm_2.homework.app.models.student import Student


class ReceivingBooks(Base):
    __tablename__ = 'receiving_books'

    receipt_id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey('books.book_id'))
    student_id: Mapped[int] = mapped_column(ForeignKey('students.student_id'))
    date_of_issue: Mapped[datetime] = mapped_column(default=datetime.now())
    date_of_return: Mapped[Optional[datetime]]

    book = relationship('Book', back_populates='students')
    student = relationship('Student', back_populates='books')

    def __init__(self, book, student, **kw: Any):
        super().__init__(**kw)
        self.book_id = book
        self.student_id = student

    def __repr__(self):
        return ("ReceivingBooks("
                f"\n\treceipt_id = {self.receipt_id}"
                f"\n\tbook_id = {self.book_id}"
                f"\n\tstudent_id = {self.student_id}"
                f"\n\tdate_of_issue = {self.date_of_issue}"
                f"\n\tdate_of_return = {self.date_of_return}"
                "\n)")

    @hybrid_property
    def count_date_with_book(self) -> int:
        end_date = self.date_of_return or datetime.now()
        return (end_date - self.date_of_issue).days

    @count_date_with_book.inplace.expression
    @classmethod
    def count_date_with_book(cls) -> int:
        end_date = case(
            (cls.date_of_return != None, cls.date_of_return),
            else_=func.now()
        )
        return func.julianday(end_date) - func.julianday(cls.date_of_issue)

    @classmethod
    def add_receipt(cls, book, student) -> Tuple[str, int]:
        query = select(ReceivingBooks).where(
            ReceivingBooks.book_id == book,
            ReceivingBooks.student_id == student,
            ReceivingBooks.date_of_return == None
        )
        if session.scalars(query).first():
            return f'A student with id {student} has already taken a book with id {book}', 400
        else:
            new_receipt = insert(ReceivingBooks).values(book_id=book, student_id=student)

            session.execute(new_receipt)
            session.commit()

            return f'Book with id {book} issued to student {student}', 201

    @classmethod
    def avg_count_of_receiving_books(cls, cur_month: int) -> float:
        sub_query = select(
            func.count(ReceivingBooks.book_id).label('row_count')
        ).group_by(
            ReceivingBooks.student_id
        ).having(
            extract('month', ReceivingBooks.date_of_issue) == cur_month
        ).subquery()

        result = session.scalar(func.avg(sub_query.c.row_count))

        return result

    @classmethod
    def debtors_list(cls) -> Optional[List['ReceivingBooks']]:
        days = 14
        query = select(ReceivingBooks).where(ReceivingBooks.count_date_with_book > days)
        return session.scalars(query).all()

    @classmethod
    def most_reading_students(cls, cur_year: int) -> Optional[List[Tuple['Student', int]]]:
        query = select(
            Student,
            func.count(ReceivingBooks.date_of_issue).label('row_count')
        ).join(
            ReceivingBooks,
            Student.books
        ).group_by(
            ReceivingBooks.student_id
        ).having(
            extract('year', ReceivingBooks.date_of_issue) == cur_year
        ).order_by(
            desc('row_count'),
            desc(func.count(ReceivingBooks.date_of_return))
        )

        students = session.execute(query).fetchmany(10)

        return students

    @classmethod
    def return_book(cls, book: int, student: int) -> Tuple[str, int]:
        try:
            query = select(
                ReceivingBooks
            ).where(
                ReceivingBooks.book_id == book,
                ReceivingBooks.student_id == student,
                ReceivingBooks.date_of_return == None
            )
            session.scalars(query).one()

            update_query = update(ReceivingBooks).where(
                ReceivingBooks.book_id == book,
                ReceivingBooks.student_id == student
            ).values(date_of_return=datetime.now())

            session.execute(update_query)
            session.commit()

            return f'Book with id {book} was returned', 200
        except NoResultFound:
            return f'Student {student} did not take book {book}', 404
        except MultipleResultsFound:
            return f'Found more than one entry with input (book={book}, student={student})', 400

    def to_json(self) -> Dict[str, Any]:
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
