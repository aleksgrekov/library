import re
from csv import DictReader
from typing import Dict, Any, Union, Optional, List

from sqlalchemy import Text, select, UniqueConstraint, event
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.orm import relationship, Mapped, mapped_column

from module_21_orm_2.homework.app.models.init import Base, session


class Student(Base):
    __tablename__ = 'students'

    student_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    surname: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text)
    average_score: Mapped[float]
    scholarship: Mapped[bool]

    books = relationship(
        'ReceivingBooks',
        back_populates='student',
        cascade='all',
        lazy='subquery'
    )

    books_titles: AssociationProxy[List[str]] = association_proxy(
        'books',
        'book.name')
    books_author: AssociationProxy[List[str]] = association_proxy(
        'books',
        'book.author_id')

    __table_args__ = (
        UniqueConstraint('name', 'surname', 'phone', name='student_unique_key'),
        UniqueConstraint('email', name='email_unique_key')
    )

    def __init__(self, name, surname, phone, email, average_score, scholarship, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.surname = surname
        self.phone = phone
        self.email = email
        self.average_score = average_score
        self.scholarship = scholarship

    def __repr__(self):
        return ("Student("
                f"\n\tstudent_id = {self.student_id}"
                f"\n\tname = {self.name}"
                f"\n\tsurname = {self.surname}"
                f"\n\tphone = {self.phone}"
                f"\n\temail = {self.email}"
                f"\n\taverage_score = {self.average_score}"
                f"\n\tscholarship = {self.scholarship}"
                "\n)")

    @classmethod
    def add_students_from_csv(cls, data: Union[DictReader, list]) -> None:
        session.bulk_insert_mappings(Student, data)
        session.commit()

    @classmethod
    def add_new_student(cls, student: 'Student') -> None:
        session.add(student)
        session.commit()

    @classmethod
    def student_by_id(cls, student_id) -> Optional['Student']:
        return session.scalar(select(Student).where(Student.student_id == student_id))

    @classmethod
    def students_with_dormitory(cls) -> Union[List['Student'], str]:
        students = session.scalars(select(Student).where(Student.scholarship is True)).all()
        if students:
            return students
        return "At the moment there are no students having a dormitory"

    @classmethod
    def students_by_average_score(cls, average_score: float) -> Union[List['Student'], str]:
        students = session.scalars(select(Student).where(Student.average_score > average_score)).all()
        if students:
            return students
        return f"There are currently no students with an average score higher than {average_score}"

    def to_json(self) -> Dict[str, Any]:
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


@event.listens_for(Student, 'before_insert')
def validate_phone(mapper, connection, target):
    phone = target.phone
    if not re.match(r'\+79\d{9}', phone):
        raise ValueError(f'Invalid phone number: {phone}.\nEnter the number in the format +79*********')


@event.listens_for(Student, 'before_insert')
def validate_and_format_email(mapper, connection, target):
    email = target.email
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValueError(f"Invalid email address: {email}. It must be a valid email format.")
    target.email = email.lower()
