import csv
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from sqlalchemy.exc import IntegrityError, PendingRollbackError
from werkzeug.utils import secure_filename

from module_21_orm_2.homework.app.models.init import Base, engine
from module_21_orm_2.homework.app.models.prepare_data import insert_data
from module_21_orm_2.homework.app.models.book import Book
from module_21_orm_2.homework.app.models.receiving_books import ReceivingBooks
from module_21_orm_2.homework.app.models.student import Student

UPLOAD_FOLDER = Path('downloads/')
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename) -> bool:
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/library/get_all', methods=['GET'])
def get_all_books():
    books = Book.all_books()

    if books:
        return jsonify(
            book_list=[book.to_json() for book in books]
        ), 200
    else:
        return 'There are no books in the library', 404


@app.route('/library/avg_count_of_receiving_books', methods=['GET'])
def get_avg_count():
    cur_date = datetime.now()
    cur_date_str = cur_date.strftime("%d-%m-%Y")

    avg_count = ReceivingBooks.avg_count_of_receiving_books(cur_date.month)

    if avg_count:
        return (
            'Average count of books students borrowed this month = {avg_count}'
            '\nRequest date: {rec_date}'
        ).format(
            avg_count=round(avg_count, 2),
            rec_date=cur_date_str
        ), 200
    else:
        return (
            'Students did not take books this month'
            '\nRequest date: {rec_date}'
        ).format(
            rec_date=cur_date_str
        ), 404


@app.route('/library/book_recommendations', methods=['GET'])
def get_book_recommendations():
    student_id = request.args.get('student_id', type=int)
    recommendations_data = Book.recommendations_for_student(student_id)

    if isinstance(recommendations_data, list):
        return jsonify(
            recommendations=[book.to_json() for book in recommendations_data]
        ), 200
    else:
        return recommendations_data


@app.route('/library/debtors', methods=['GET'])
def get_debtors():
    deb_list = ReceivingBooks.debtors_list()

    if deb_list:
        return jsonify(
            list_of_debtors=[deb.to_json() for deb in deb_list]
        )
    else:
        return 'No students failed their books', 404


@app.route('/library/get_by_name', methods=['GET'])
def get_books_by_title():
    title = request.args.get('title', type=str)
    books = Book.book_by_name(title=title)

    if books:
        return jsonify(
            book_list=[book.to_json() for book in books]
        ), 200
    else:
        return f'There is no book with title {title} in the library', 404


@app.route('/library/most_popular_book', methods=['GET'])
def get_most_popular_book():
    book_data, rec_count = Book.most_popular_book()
    if book_data:
        most_popular_book = book_data.to_json()
        most_popular_book['rec_count'] = rec_count

        return jsonify(most_popular_book=most_popular_book), 200
    else:
        return 'There are no books in the library yet', 404


@app.route('/library/most_reading_students', methods=['GET'])
def get_most_reading_students():
    cur_date = datetime.now()
    students = list()

    for student, read_books in ReceivingBooks.most_reading_students(cur_year=cur_date.year):
        student_as_dict = student.to_json()
        student_as_dict['read_books'] = read_books
        students.append(student_as_dict)

    if students:
        return jsonify(most_reading_students=students), 200
    else:
        return 'There are no students data in the database yet', 404


@app.route('/library/sum_of_books_by_author', methods=['GET'])
def get_sum_of_books_by_author():
    author_id = request.args.get('author_id', type=int)
    sum_of_books = Book.sum_of_books_by_author_id(author_id=author_id)

    if sum_of_books:
        return f'The author with id {author_id} has {sum_of_books} books in the library', 200
    else:
        return 'There are no books by this author in the library', 404


@app.route('/library/add_students_from_file', methods=['POST'])
def add_students_from_file():
    if 'files' not in request.files:
        return 'File not found', 404

    file = request.files['files']

    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        if not app.config['UPLOAD_FOLDER'].exists() or not app.config['UPLOAD_FOLDER'].is_dir():
            os.mkdir(app.config['UPLOAD_FOLDER'])

        file.save(app.config['UPLOAD_FOLDER'] / filename)
        with open(Path(f'downloads/{filename}'), newline='') as student_file:
            data = list()
            reader = csv.DictReader(student_file, delimiter=';')

            for row in reader:
                row['scholarship'] = (row['scholarship'] == 'True')
                data.append(row)

            try:
                Student.add_students_from_csv(data)
            except (IntegrityError, PendingRollbackError):
                return 'The students are already in database', 400

        return 'Students added successfully', 201
    return 'Wrong file', 400


@app.route('/library/add_new_student', methods=['POST'])
def add_new_student():
    data = request.json
    if not data:
        return 'There is no data', 404

    try:
        student = Student(**data)
        Student.add_new_student(student)
    except ValueError as exc:
        return f'{exc}', 400
    except TypeError as exc:
        message = f'{exc}'.split(' ', 1)
        return f'{message[1]}', 400
    except IntegrityError as exc:
        message = f'{exc.args[0]}'.split(' ', 1)
        return f'{message[1]}', 400
    except PendingRollbackError:
        return 'Failed to insert data', 400

    return 'Student added successfully', 201


@app.route('/library/give_book', methods=['POST'])
def give_book():
    book_id = request.form.get('book_id', type=int)
    student_id = request.form.get('student_id', type=int)

    res = ReceivingBooks.add_receipt(book=book_id, student=student_id)
    return res


@app.route('/library/return_book', methods=['POST'])
def return_book():
    book_id = request.form.get('book_id', type=int)
    student_id = request.form.get('student_id', type=int)

    res = ReceivingBooks.return_book(book=book_id, student=student_id)
    return res


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    insert_data()
    app.run(debug=False, port=8080)
