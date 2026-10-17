CREATE DATABASE BibliotecaUNII;

USE BibliotecaUNII

CREATE TABLE Usuario (
    id_usuario INT IDENTITY(1,1) PRIMARY KEY,
    usuario_login VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'Usuario',
    activo BIT DEFAULT 1
);


CREATE TABLE Libros (
    id_libro INT IDENTITY(1,1) PRIMARY KEY,
    ISBN VARCHAR(20),
    Titulo NVARCHAR(200) NOT NULL,
    Autor NVARCHAR(150),
    AnioPublicacion INT,
    Imagen_URL VARCHAR(500),
    estado VARCHAR(50) DEFAULT 'Disponible'
);

CREATE TABLE Ejemplar (
    id_ejemplar INT PRIMARY KEY,
    id_libro INT NOT NULL,
    estado VARCHAR(50) DEFAULT 'Disponible',
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro)
);


CREATE TABLE Prestamos (
    id_Prestamo INT IDENTITY(1,1) PRIMARY KEY,
    id_Usuario INT NOT NULL,
    id_Ejemplar INT NULL,
    fecha_Solicitud DATE DEFAULT GETDATE(),
    fecha_Devolucion DATE,
    estado VARCHAR(50) DEFAULT 'activo',
    eliminado BIT DEFAULT 0,
    FOREIGN KEY (id_Usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_Ejemplar) REFERENCES Ejemplar(id_ejemplar)
);


CREATE TABLE Recibos (
    id_Recibo INT IDENTITY(1,1) PRIMARY KEY,
    id_Prestamo INT NOT NULL,
    fecha_Emision DATE DEFAULT GETDATE(),
    FOREIGN KEY (id_Prestamo) REFERENCES Prestamos(id_Prestamo)
);

CREATE TABLE PrestamoDetalle (
    id_Detalle INT IDENTITY(1,1) PRIMARY KEY,
    id_Prestamo INT NOT NULL,
    id_Libro INT NOT NULL,
    FOREIGN KEY (id_Prestamo) REFERENCES Prestamos(id_Prestamo),
    FOREIGN KEY (id_Libro) REFERENCES Libros(id_libro)
);

CREATE TABLE Comentarios (
    id_comentario INT IDENTITY(1,1) PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_libro INT NOT NULL,
    calificacion INT CHECK (calificacion BETWEEN 1 AND 5),
    comentario VARCHAR(1000),
    fecha DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario),
    FOREIGN KEY (id_libro) REFERENCES Libros(id_libro)
);

SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'Usuario';

INSERT INTO Libros (ISBN, Titulo, Autor, AnioPublicacion, Imagen_URL, estado) VALUES 
('978-0-06-112008-4', 'To Kill a Mockingbird', 'Harper Lee', 1960, 'https://covers.openlibrary.org/b/isbn/9780061120084-L.jpg', 'Disponible'),
('978-0-7432-7356-5', '1984', 'George Orwell', 1949, 'https://covers.openlibrary.org/b/isbn/9780451524935-L.jpg', 'Disponible'),
('978-0-7432-7357-2', 'Animal Farm', 'George Orwell', 1945, 'https://covers.openlibrary.org/b/isbn/9780452284241-L.jpg', 'Disponible'),
('978-0-14-017739-8', 'The Great Gatsby', 'F. Scott Fitzgerald', 1925, 'https://covers.openlibrary.org/b/isbn/9780743273565-L.jpg', 'Disponible'),
('978-0-316-76948-0', 'The Catcher in the Rye', 'J.D. Salinger', 1951, 'https://covers.openlibrary.org/b/isbn/9780316769488-L.jpg', 'Disponible'),
('978-0-679-72021-8', 'The Hobbit', 'J.R.R. Tolkien', 1937, 'https://covers.openlibrary.org/b/isbn/9780547928227-L.jpg', 'Disponible'),
('978-0-618-64015-7', 'The Lord of the Rings', 'J.R.R. Tolkien', 1954, 'https://covers.openlibrary.org/b/isbn/9780618640157-L.jpg', 'Disponible'),
('978-0-553-21311-7', 'A Game of Thrones', 'George R.R. Martin', 1996, 'https://covers.openlibrary.org/b/isbn/9780553103540-L.jpg', 'Disponible'),
('978-0-06-093546-9', 'The Alchemist', 'Paulo Coelho', 1988, 'https://covers.openlibrary.org/b/isbn/9780061122415-L.jpg', 'Disponible'),
('978-0-385-33348-1', 'The Da Vinci Code', 'Dan Brown', 2003, 'https://covers.openlibrary.org/b/isbn/9780385504201-L.jpg', 'Disponible'),
('978-0-7432-7358-9', 'The Hunger Games', 'Suzanne Collins', 2008, 'https://covers.openlibrary.org/b/isbn/9780439023481-L.jpg', 'Disponible'),
('978-0-545-01022-1', 'Harry Potter and the Sorcerer''s Stone', 'J.K. Rowling', 1997, 'https://covers.openlibrary.org/b/isbn/9780590353427-L.jpg', 'Disponible'),
('978-0-307-47612-1', 'The Girl with the Dragon Tattoo', 'Stieg Larsson', 2005, 'https://covers.openlibrary.org/b/isbn/9780307454546-L.jpg', 'Disponible'),
('978-0-446-61009-4', 'The Shining', 'Stephen King', 1977, 'https://covers.openlibrary.org/b/isbn/9780307743657-L.jpg', 'Disponible'),
('978-0-525-47881-2', 'Educated', 'Tara Westover', 2018, 'https://covers.openlibrary.org/b/isbn/9780399590504-L.jpg', 'Disponible'),
('978-0-316-76949-7', 'The Martian', 'Andy Weir', 2011, 'https://covers.openlibrary.org/b/isbn/9780553418026-L.jpg', 'Disponible'),
('978-0-06-085052-4', 'The Kite Runner', 'Khaled Hosseini', 2003, 'https://covers.openlibrary.org/b/isbn/9781594631931-L.jpg', 'Disponible'),
('978-0-14-303943-3', 'The Life of Pi', 'Yann Martel', 2001, 'https://covers.openlibrary.org/b/isbn/9780156027328-L.jpg', 'Disponible'),
('978-0-7432-7359-6', 'The Fault in Our Stars', 'John Green', 2012, 'https://covers.openlibrary.org/b/isbn/9780525478812-L.jpg', 'Disponible'),
('978-0-06-112009-1', 'Go Set a Watchman', 'Harper Lee', 2015, 'https://covers.openlibrary.org/b/isbn/9780062409850-L.jpg', 'Disponible');


INSERT INTO Usuario (usuario_login, contrasena, rol, activo) VALUES 
('admin', 'admin123', 'Admin', 1),
('juan_perez', 'juan123', 'Usuario', 1),
('maria_gomez', 'maria123', 'Usuario', 1);


INSERT INTO Ejemplar (id_ejemplar, id_libro, estado)
SELECT 
    667382 + ROW_NUMBER() OVER (ORDER BY id_libro) AS id_ejemplar,
    id_libro,
    'Disponible'
FROM Libros;




ALTER TABLE Usuario ADD foto_perfil VARCHAR(500) NULL;



SELECT 'Libros' AS Tabla, COUNT(*) AS Total FROM Libros
UNION ALL SELECT 'Usuario', COUNT(*) FROM Usuario
UNION ALL SELECT 'Ejemplar', COUNT(*) FROM Ejemplar;





SELECT id_usuario, usuario_login, contrasena, rol FROM Usuario;