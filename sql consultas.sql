--SELECT BASICO
USE BibliotecaUNI;

SELECT id_libro, Titulo, Autor, AnioPublicacion
FROM Libros
ORDER BY Titulo;

--SELECT WHERE
USE BibliotecaUNI;

SELECT Titulo, Autor, AnioPublicacion
FROM Libros
WHERE AnioPublicacion > 2000
ORDER BY AnioPublicacion DESC;

--SELECT CON INNER JOIN
USE BibliotecaUNI;

SELECT e.id_ejemplar, l.Titulo, e.estado
FROM Ejemplar e
INNER JOIN Libros l ON e.id_libro = l.id_libro
ORDER BY l.Titulo;

--GROUP BY Y ORDER BY
USE BibliotecaUNI;

SELECT l.Titulo, COUNT(e.id_ejemplar) AS Total_Ejemplares
FROM Libros l
INNER JOIN Ejemplar e ON l.id_libro = e.id_libro
GROUP BY l.Titulo
ORDER BY Total_Ejemplares DESC;

--CONDICIONES MULTIPLES
USE BibliotecaUNI;

SELECT Titulo, Autor, AnioPublicacion
FROM Libros
WHERE Autor = 'George Orwell' AND AnioPublicacion < 1950;

--LIBROS MA PRETADOS (TOP 5)
USE BibliotecaUNI;

SELECT TOP 5 
    l.Titulo, 
    COUNT(pd.id_Detalle) AS Veces_Prestado
FROM Libros l
INNER JOIN PrestamoDetalle pd ON l.id_libro = pd.id_Libro
GROUP BY l.Titulo
ORDER BY Veces_Prestado DESC;

--PRESTAMO POR USUARIO
USE BibliotecaUNI;

SELECT 
    u.usuario_login, 
    COUNT(p.id_Prestamo) AS Total_Prestamos
FROM Usuario u
INNER JOIN Prestamos p ON u.id_usuario = p.id_Usuario
GROUP BY u.usuario_login
ORDER BY Total_Prestamos DESC;

--PRESTAMOS ACTIVOS
USE BibliotecaUNI;

SELECT 
    p.id_Prestamo, 
    u.usuario_login, 
    l.Titulo,
    p.fecha_Solicitud, 
    p.fecha_Devolucion
FROM Prestamos p
INNER JOIN Usuario u ON p.id_Usuario = u.id_usuario
INNER JOIN PrestamoDetalle pd ON p.id_Prestamo = pd.id_Prestamo
INNER JOIN Libros l ON pd.id_Libro = l.id_libro
WHERE p.estado = 'activo' AND p.eliminado = 0
ORDER BY p.fecha_Solicitud DESC;

--UPDATE
USE BibliotecaUNI;

UPDATE Ejemplar 
SET estado = 'Disponible' 
WHERE id_ejemplar = 667383;

SELECT id_ejemplar, id_libro, estado 
FROM Ejemplar 
WHERE id_ejemplar = 667383;

--DELETE
USE BibliotecaUNI;

SELECT * FROM PrestamoDetalle 
WHERE id_Detalle = 99999;

DELETE FROM PrestamoDetalle 
WHERE id_Detalle = 99999;

SELECT * FROM PrestamoDetalle 
WHERE id_Detalle = 99999;



---CONSULTA EL HAS DEL USUARIO
USE BibliotecaUNI;

SELECT usuario_login, password_hash
FROM Usuario
WHERE usuario_login = 'juan_perez';



--CONSULTA DE USUARIOS
USE BibliotecaUNI;

SELECT id_usuario, usuario_login, rol, activo
FROM Usuario
ORDER BY id_usuario;

--RECIBOS
SELECT * FROM Recibos;

---prestamos activos
USE BibliotecaUNI;

SELECT COUNT(*) AS total_prestamos FROM Prestamos;



