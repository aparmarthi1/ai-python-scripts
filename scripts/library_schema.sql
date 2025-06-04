
-- Library Schema for PostgreSQL and Oracle
-- Creates Authors, Books, and Borrowers tables with sample data

CREATE TABLE Authors (
    author_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name VARCHAR2(50),
    last_name VARCHAR2(50),
    nationality VARCHAR2(50)
);

CREATE TABLE Books (
    book_id NUMBER PRIMARY KEY,
    title VARCHAR2(100),
    author_id NUMBER,
    publication_year NUMBER,
    genre VARCHAR2(50),
    CONSTRAINT fk_author FOREIGN KEY (author_id) REFERENCES Authors(author_id)
);

CREATE TABLE Borrowers (
    borrower_id NUMBER PRIMARY KEY,
    book_id NUMBER,
    borrower_name VARCHAR2(100),
    borrow_date DATE,
    CONSTRAINT fk_book FOREIGN KEY (book_id) REFERENCES Books(book_id)
);

INSERT INTO Authors (first_name, last_name, nationality) VALUES
('George', 'Orwell', 'British'),
('J.K.', 'Rowling', 'British');

INSERT INTO Books (book_id, title, author_id, publication_year, genre) VALUES
(1, '1984', 1, 1949, 'Dystopian'),
(2, 'Animal Farm', 1, 1945, 'Satire'),
(3, 'Harry Potter and the Sorcerer''s Stone', 2, 1997, 'Fantasy');

INSERT INTO Borrowers (borrower_id, book_id, borrower_name, borrow_date) VALUES
(1, 1, 'Alice Smith', TO_DATE('2025-05-01', 'YYYY-MM-DD')),
(2, 3, 'Bob Johnson', TO_DATE('2025-05-15', 'YYYY-MM-DD')),
(3, 3, 'Charlie Brown', TO_DATE('2025-05-10', 'YYYY-MM-DD'));
