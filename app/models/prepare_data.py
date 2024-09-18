import random
from datetime import date, datetime, timedelta
from statistics import mean

from sqlalchemy import select

from module_21_orm_2.homework.app.models.author import Author
from module_21_orm_2.homework.app.models.book import Book
from module_21_orm_2.homework.app.models.init import session
from module_21_orm_2.homework.app.models.receiving_books import ReceivingBooks
from module_21_orm_2.homework.app.models.student import Student


def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)


def insert_data():
    if not session.scalars(select(Author)).all():

        authors_list = [
            Author(name='Лев', surname='Толстой'),
            Author(name='Уильям', surname='Шекспир'),
            Author(name='Владимир', surname='Набоков'),
            Author(name='Фёдор', surname='Достоевский'),
            Author(name='Чарльз', surname='Диккенс'),
            Author(name='Антон', surname='Чехов'),
            Author(name='Джейн', surname='Остин')
        ]
        books_list = [
            [
                Book(
                    title='Война и мир',
                    count=random.randint(1, 10),
                    release_date=date(1867, 1, 1)
                ),
                Book(
                    title='Анна Каренина',
                    count=random.randint(1, 10),
                    release_date=date(1873, 1, 1)
                ),
                Book(
                    title='Чем люди живы',
                    count=random.randint(1, 10),
                    release_date=date(1885, 1, 1)
                )
            ],
            [
                Book(
                    title='Гамлет',
                    count=random.randint(1, 10),
                    release_date=date(1601, 1, 1)
                ),
                Book(
                    title='Ромео и Джульетта',
                    count=random.randint(1, 10),
                    release_date=date(1595, 1, 1)
                ),
                Book(
                    title='Макбет',
                    count=random.randint(1, 10),
                    release_date=date(1606, 1, 1)
                )
            ],
            [
                Book(
                    title='Лолита',
                    count=random.randint(1, 10),
                    release_date=date(1955, 1, 1)
                )

            ],
            [
                Book(
                    title='Преступление и наказание',
                    count=random.randint(1, 10),
                    release_date=date(1866, 1, 1)
                ),
                Book(
                    title='Братья Карамазовы',
                    count=random.randint(1, 10),
                    release_date=date(1880, 1, 1)
                )
            ],
            [
                Book(
                    title='Тяжелые времена',
                    count=random.randint(1, 10),
                    release_date=date(1854, 1, 1)
                )
            ],
            [
                Book(
                    title='Хамелеон',
                    count=random.randint(1, 10),
                    release_date=date(1884, 1, 1)
                ),
                Book(
                    title='Мальчики',
                    count=random.randint(1, 10),
                    release_date=date(1887, 1, 1)
                )
            ],
            [
                Book(
                    title='Гордость и предубеждение',
                    count=random.randint(1, 10),
                    release_date=date(1813, 1, 1)
                )
            ],

        ]

        for author, book in zip(authors_list, books_list):
            author.books.extend(book)
        session.add_all(authors_list)

        student_names = [
            'David Phillips',
            'David Kelly',
            'Thomas Simmons',
            'Joseph Hammond',
            'Marie McBride',
            'Michelle Walker',
            'James Huff',
            'Patrick Ramirez',
            'Dorothy James',
            'Heidi Hodges',
        ]
        students_list = [
            Student(
                name=names.split()[0],
                surname=names.split()[1],
                phone=f'+79{''.join([str(random.randint(0, 9)) for _ in range(9)])}',
                email=f'testemail{random.randint(1, 100)}@{random.choice(['mail', 'inbox', 'yandex', 'bk'])}.ru',
                average_score=round(mean([random.randint(1, 10) for _ in range(30)]), 2),
                scholarship=bool(random.getrandbits(1))
            )
            for names in student_names
        ]

        session.add_all(students_list)

        receipts_list = list()
        for _ in range(15):
            receipt = ReceivingBooks(
                book=random.choice([b[0] for b in session.query(Book.book_id).all()]),
                student=random.choice([s[0] for s in session.query(Student.student_id).all()])
            )
            receipt.date_of_issue = random_date(
                datetime(2024, 6, 15, 12, 00),
                datetime(2024, 7, 10, 17, 00)
            )
            receipt.date_of_return = random.choice(
                [
                    random_date(
                        datetime(2024, 7, 11, 12, 00),
                        datetime.now()
                    ),
                    None
                ]
            )
            receipts_list.append(receipt)

        session.add_all(receipts_list)

        session.commit()
