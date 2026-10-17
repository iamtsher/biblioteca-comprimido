from database import get_connection
from datetime import datetime, timedelta


class Usuario:
    def __init__(self, id_usuario=None, usuario_login="", contrasena="",
                 rol="Usuario", activo=True, foto_perfil=None):
        self.id_usuario = id_usuario
        self.usuario_login = usuario_login
        self.contrasena = contrasena
        self.rol = rol
        self.activo = activo
        self.foto_perfil = foto_perfil

    @staticmethod
    def _from_row(fila):
        if not fila:
            return None
        return Usuario(
            id_usuario=fila[0],
            usuario_login=fila[1],
            contrasena=fila[2],
            rol=fila[3] if len(fila) > 3 else "Usuario",
            activo=bool(fila[4]) if len(fila) > 4 else True,
            foto_perfil=fila[5] if len(fila) > 5 else None
        )

    @staticmethod
    def verificar_login(usuario_login, contrasena):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, usuario_login, contrasena, rol, activo, foto_perfil
            FROM Usuario
            WHERE usuario_login = ? AND contrasena = ? AND activo = 1
        """, (usuario_login, contrasena))
        fila = cursor.fetchone()
        conn.close()
        return Usuario._from_row(fila)

    @staticmethod
    def obtener_por_login(usuario_login):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, usuario_login, contrasena, rol, activo, foto_perfil
            FROM Usuario
            WHERE usuario_login = ? AND activo = 1
        """, (usuario_login,))
        fila = cursor.fetchone()
        conn.close()
        return Usuario._from_row(fila)

    @staticmethod
    def obtener_todos():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, usuario_login, contrasena, rol, activo, foto_perfil
            FROM Usuario
            WHERE activo = 1
            ORDER BY usuario_login
        """)
        filas = cursor.fetchall()
        conn.close()
        return [Usuario._from_row(f) for f in filas]

    @staticmethod
    def obtener_eliminados():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, usuario_login, contrasena, rol, activo, foto_perfil
            FROM Usuario
            WHERE activo = 0
            ORDER BY usuario_login
        """)
        filas = cursor.fetchall()
        conn.close()
        return [Usuario._from_row(f) for f in filas]

    @staticmethod
    def obtener_por_id(id_usuario):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_usuario, usuario_login, contrasena, rol, activo, foto_perfil
            FROM Usuario
            WHERE id_usuario = ?
        """, (id_usuario,))
        fila = cursor.fetchone()
        conn.close()
        return Usuario._from_row(fila)

    @staticmethod
    def contar():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Usuario WHERE activo = 1")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def tiene_prestamos_vencidos(id_usuario):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM Prestamos
            WHERE id_Usuario = ?
            AND estado = 'activo'
            AND fecha_Devolucion < CAST(GETDATE() AS DATE)
        """, (id_usuario,))
        total = cursor.fetchone()[0]
        conn.close()
        return total > 0

    def guardar(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            if self.id_usuario:
                cursor.execute("""
                    UPDATE Usuario
                    SET usuario_login = ?, contrasena = ?, rol = ?, activo = ?, foto_perfil = ?
                    WHERE id_usuario = ?
                """, (self.usuario_login, self.contrasena, self.rol,
                      1 if self.activo else 0, self.foto_perfil, self.id_usuario))
            else:
                cursor.execute("""
                    INSERT INTO Usuario (usuario_login, contrasena, rol, activo, foto_perfil)
                    OUTPUT INSERTED.id_usuario
                    VALUES (?, ?, ?, 1, ?)
                """, (self.usuario_login, self.contrasena, self.rol, self.foto_perfil))
                fila = cursor.fetchone()
                if fila:
                    self.id_usuario = int(fila[0])
            conn.commit()
            return self.id_usuario
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def eliminar(self):
        if self.id_usuario:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Usuario SET activo = 0 WHERE id_usuario = ?",
                           (self.id_usuario,))
            conn.commit()
            conn.close()

    def restaurar(self):
        if self.id_usuario:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Usuario SET activo = 1 WHERE id_usuario = ?",
                           (self.id_usuario,))
            conn.commit()
            conn.close()

    def eliminar_definitivo(self):
        if self.id_usuario:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Usuario WHERE id_usuario = ?",
                           (self.id_usuario,))
            conn.commit()
            conn.close()


class Libro:
    def __init__(self, idLibro=None, ISBN=None, Book_Title="", Book_Author="",
                 Year_Of_Publication=None, Publisher="", Image_URL_L="",
                 estado="Disponible"):
        self.idLibro = idLibro
        self.ISBN = ISBN
        self.Book_Title = Book_Title
        self.Book_Author = Book_Author
        self.Year_Of_Publication = Year_Of_Publication
        self.Publisher = Publisher
        self.Image_URL_L = Image_URL_L
        self.estado = estado

    @staticmethod
    def _from_row(fila):
        if not fila:
            return None
        return Libro(
            idLibro=fila[0],
            ISBN=fila[1],
            Book_Title=fila[2],
            Book_Author=fila[3],
            Year_Of_Publication=fila[4],
            Image_URL_L=fila[5],
            estado=fila[6] if len(fila) > 6 else "Disponible"
        )

    @staticmethod
    def obtener_todos(limit=5000):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP {limit} id_libro, ISBN, Titulo, Autor,
                   AnioPublicacion, Imagen_URL, estado
            FROM Libros
            ORDER BY Titulo
        """)
        filas = cursor.fetchall()
        conn.close()
        return [Libro._from_row(f) for f in filas]

    @staticmethod
    def contar():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Libros")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def buscar(termino=""):
        conn = get_connection()
        cursor = conn.cursor()
        t = f"%{termino}%"
        cursor.execute("""
            SELECT TOP 5000 id_libro, ISBN, Titulo, Autor,
                   AnioPublicacion, Imagen_URL, estado
            FROM Libros
            WHERE Titulo LIKE ? OR Autor LIKE ? OR ISBN LIKE ?
            ORDER BY Titulo
        """, (t, t, t))
        filas = cursor.fetchall()
        conn.close()
        return [Libro._from_row(f) for f in filas]

    @staticmethod
    def obtener_por_id(id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_libro, ISBN, Titulo, Autor,
                   AnioPublicacion, Imagen_URL, estado
            FROM Libros
            WHERE id_libro = ?
        """, (id_libro,))
        fila = cursor.fetchone()
        conn.close()
        return Libro._from_row(fila)

    def guardar(self):
        conn = get_connection()
        cursor = conn.cursor()
        if self.idLibro:
            cursor.execute("""
                UPDATE Libros
                SET ISBN = ?, Titulo = ?, Autor = ?,
                    AnioPublicacion = ?, Imagen_URL = ?, estado = ?
                WHERE id_libro = ?
            """, (self.ISBN, self.Book_Title, self.Book_Author,
                  self.Year_Of_Publication, self.Image_URL_L,
                  self.estado, self.idLibro))
        else:
            cursor.execute("""
                INSERT INTO Libros (ISBN, Titulo, Autor, AnioPublicacion,
                                    Imagen_URL, estado)
                OUTPUT INSERTED.id_libro
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.ISBN, self.Book_Title, self.Book_Author,
                  self.Year_Of_Publication, self.Image_URL_L, self.estado))
            fila = cursor.fetchone()
            if fila:
                self.idLibro = int(fila[0])
        conn.commit()
        conn.close()
        return self.idLibro

    def eliminar(self):
        if self.idLibro:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Libros WHERE id_libro = ?",
                           (self.idLibro,))
            conn.commit()
            conn.close()

    def contar_ejemplares(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Ejemplar WHERE id_libro = ?",
                       (self.idLibro,))
        total = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COUNT(*) FROM Ejemplar
            WHERE id_libro = ? AND estado = 'Disponible'
        """, (self.idLibro,))
        disponibles = cursor.fetchone()[0]
        conn.close()
        return total, disponibles


class Ejemplar:
    def __init__(self, id_ejemplar=None, id_libro=None,
                 estado="Disponible", titulo_libro=""):
        self.id_ejemplar = id_ejemplar
        self.id_libro = id_libro
        self.estado = estado
        self.titulo_libro = titulo_libro

    @staticmethod
    def _from_row(fila):
        if not fila:
            return None
        return Ejemplar(
            id_ejemplar=fila[0],
            id_libro=fila[1],
            estado=fila[2],
            titulo_libro=fila[3] if len(fila) > 3 else ""
        )

    @staticmethod
    def contar():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Ejemplar")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def contar_disponibles():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Ejemplar WHERE estado = 'Disponible'")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def obtener_todos(limit=5000):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP {limit} e.id_ejemplar, e.id_libro, e.estado,
                   l.Titulo AS titulo_libro
            FROM Ejemplar e
            JOIN Libros l ON e.id_libro = l.id_libro
            ORDER BY e.id_ejemplar
        """)
        filas = cursor.fetchall()
        conn.close()
        return [Ejemplar._from_row(f) for f in filas]

    @staticmethod
    def obtener_por_libro(id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id_ejemplar, e.id_libro, e.estado,
                   l.Titulo AS titulo_libro
            FROM Ejemplar e
            JOIN Libros l ON e.id_libro = l.id_libro
            WHERE e.id_libro = ?
            ORDER BY e.id_ejemplar
        """, (id_libro,))
        filas = cursor.fetchall()
        conn.close()
        return [Ejemplar._from_row(f) for f in filas]

    @staticmethod
    def obtener_disponibles_por_libro(id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id_ejemplar, e.id_libro, e.estado,
                   l.Titulo AS titulo_libro
            FROM Ejemplar e
            JOIN Libros l ON e.id_libro = l.id_libro
            WHERE e.id_libro = ? AND e.estado = 'Disponible'
            ORDER BY e.id_ejemplar
        """, (id_libro,))
        filas = cursor.fetchall()
        conn.close()
        return [Ejemplar._from_row(f) for f in filas]

    @staticmethod
    def obtener_por_id(id_ejemplar):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id_ejemplar, e.id_libro, e.estado,
                   l.Titulo AS titulo_libro
            FROM Ejemplar e
            JOIN Libros l ON e.id_libro = l.id_libro
            WHERE e.id_ejemplar = ?
        """, (id_ejemplar,))
        fila = cursor.fetchone()
        conn.close()
        return Ejemplar._from_row(fila)

    def guardar(self):
        conn = get_connection()
        cursor = conn.cursor()
        if self.id_ejemplar:
            cursor.execute("""
                UPDATE Ejemplar SET id_libro = ?, estado = ?
                WHERE id_ejemplar = ?
            """, (self.id_libro, self.estado, self.id_ejemplar))
        else:
            cursor.execute("""
                INSERT INTO Ejemplar (id_ejemplar, id_libro, estado)
                VALUES (?, ?, ?)
            """, (self.id_ejemplar, self.id_libro, self.estado))
        conn.commit()
        conn.close()
        return self.id_ejemplar

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Ejemplar SET estado = ? WHERE id_ejemplar = ?",
                       (nuevo_estado, self.id_ejemplar))
        conn.commit()
        conn.close()

    def eliminar(self):
        if self.id_ejemplar:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Ejemplar WHERE id_ejemplar = ?",
                           (self.id_ejemplar,))
            conn.commit()
            conn.close()


class Recibo:
    def __init__(self, id_recibo=None, id_prestamo=None, fecha_emision=None):
        self.id_recibo = id_recibo
        self.id_prestamo = id_prestamo
        self.fecha_emision = fecha_emision

    @staticmethod
    def _from_row(fila):
        if not fila:
            return None
        return Recibo(
            id_recibo=fila[0],
            id_prestamo=fila[1],
            fecha_emision=str(fila[2]) if fila[2] else None
        )

    @staticmethod
    def obtener_por_prestamo(id_prestamo):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TOP 1 id_Recibo, id_Prestamo, fecha_Emision
            FROM Recibos
            WHERE id_Prestamo = ?
            ORDER BY id_Recibo DESC
        """, (id_prestamo,))
        fila = cursor.fetchone()
        conn.close()
        return Recibo._from_row(fila)

    @staticmethod
    def obtener_por_id(id_recibo):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id_Recibo, id_Prestamo, fecha_Emision
            FROM Recibos
            WHERE id_Recibo = ?
        """, (id_recibo,))
        fila = cursor.fetchone()
        conn.close()
        return Recibo._from_row(fila)

    @staticmethod
    def obtener_todos(limit=5000):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT TOP {limit} id_Recibo, id_Prestamo, fecha_Emision
            FROM Recibos
            ORDER BY fecha_Emision DESC
        """)
        filas = cursor.fetchall()
        conn.close()
        return [Recibo._from_row(f) for f in filas]

    @staticmethod
    def contar():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Recibos")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def existe_para_prestamo(id_prestamo):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Recibos WHERE id_Prestamo = ?",
            (id_prestamo,))
        total = cursor.fetchone()[0]
        conn.close()
        return total > 0

    @staticmethod
    def crear(id_prestamo):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Recibos (id_Prestamo, fecha_Emision)
                OUTPUT INSERTED.id_Recibo, INSERTED.fecha_Emision
                VALUES (?, GETDATE())
            """, (id_prestamo,))
            fila = cursor.fetchone()
            conn.commit()
            if fila:
                return Recibo(
                    id_recibo=int(fila[0]),
                    id_prestamo=id_prestamo,
                    fecha_emision=str(fila[1])
                )
            return None
        except Exception:
            conn.rollback()
            return None
        finally:
            conn.close()

    @staticmethod
    def obtener_o_crear(id_prestamo):
        recibo = Recibo.obtener_por_prestamo(id_prestamo)
        if recibo:
            return recibo
        return Recibo.crear(id_prestamo)

    def eliminar(self):
        if self.id_recibo:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Recibos WHERE id_Recibo = ?",
                           (self.id_recibo,))
            conn.commit()
            conn.close()


class Prestamo:
    def __init__(self, id_prestamo=None, id_usuario=None, fecha_solicitud=None,
                 fecha_devolucion_esperada=None, estado_prestamo="activo",
                 nombre_usuario="", ejemplares_count=0):
        self.id_prestamo = id_prestamo
        self.id_usuario = id_usuario
        self.fecha_solicitud = fecha_solicitud
        self.fecha_devolucion_esperada = fecha_devolucion_esperada
        self.estado_prestamo = estado_prestamo
        self.nombre_usuario = nombre_usuario
        self.ejemplares_count = ejemplares_count

    @staticmethod
    def _from_row(fila):
        if not fila:
            return None
        return Prestamo(
            id_prestamo=fila[0],
            id_usuario=fila[1],
            fecha_solicitud=str(fila[2]) if fila[2] else None,
            fecha_devolucion_esperada=str(fila[3]) if fila[3] else None,
            estado_prestamo=fila[4],
            nombre_usuario=fila[5] if len(fila) > 5 else "",
            ejemplares_count=fila[6] if len(fila) > 6 else 0
        )

    @staticmethod
    def contar_activos():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM Prestamos
            WHERE estado = 'activo' AND eliminado = 0
        """)
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def contar_historial():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Prestamos WHERE eliminado = 0")
        total = cursor.fetchone()[0]
        conn.close()
        return total

    @staticmethod
    def _consulta_base(where=""):
        return f"""
            SELECT p.id_Prestamo, p.id_Usuario, p.fecha_Solicitud,
                   p.fecha_Devolucion, p.estado,
                   u.usuario_login AS nombre_usuario,
                   (SELECT COUNT(*) FROM PrestamoDetalle pd
                    WHERE pd.id_Prestamo = p.id_Prestamo) AS ejemplares_count
            FROM Prestamos p
            JOIN Usuario u ON p.id_Usuario = u.id_usuario
            {where}
            ORDER BY p.fecha_Solicitud DESC
        """

    @staticmethod
    def obtener_activos():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(Prestamo._consulta_base(
            "WHERE p.estado = 'activo' AND p.eliminado = 0"
        ))
        filas = cursor.fetchall()
        conn.close()
        return [Prestamo._from_row(f) for f in filas]

    @staticmethod
    def obtener_historial():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(Prestamo._consulta_base("WHERE p.eliminado = 0"))
        filas = cursor.fetchall()
        conn.close()
        return [Prestamo._from_row(f) for f in filas]

    @staticmethod
    def obtener_eliminados():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(Prestamo._consulta_base("WHERE p.eliminado = 1"))
        filas = cursor.fetchall()
        conn.close()
        return [Prestamo._from_row(f) for f in filas]

    @staticmethod
    def obtener_por_id(id_prestamo):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id_Prestamo, p.id_Usuario, p.fecha_Solicitud,
                   p.fecha_Devolucion, p.estado,
                   u.usuario_login AS nombre_usuario
            FROM Prestamos p
            JOIN Usuario u ON p.id_Usuario = u.id_usuario
            WHERE p.id_Prestamo = ?
        """, (id_prestamo,))
        fila = cursor.fetchone()
        conn.close()
        return Prestamo._from_row(fila)

    @staticmethod
    def mover_devueltos_a_papelera():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE Prestamos SET eliminado = 1
                WHERE estado = 'devuelto' AND eliminado = 0
            """)
            conn.commit()
            return True, "Préstamos devueltos movidos a la papelera."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {e}"
        finally:
            conn.close()

    @staticmethod
    def mover_todo_a_papelera():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Prestamos SET eliminado = 1 WHERE eliminado = 0")
            conn.commit()
            return True, "Todo el historial movido a la papelera."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {e}"
        finally:
            conn.close()

    @staticmethod
    def restaurar_todo():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Prestamos SET eliminado = 0 WHERE eliminado = 1")
            conn.commit()
            return True, "Historial restaurado completamente."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {e}"
        finally:
            conn.close()

    @staticmethod
    def eliminar_definitivo_todo():
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM Recibos
                WHERE id_Prestamo IN (
                    SELECT id_Prestamo FROM Prestamos WHERE eliminado = 1
                )
            """)
            cursor.execute("""
                DELETE FROM PrestamoDetalle
                WHERE id_Prestamo IN (
                    SELECT id_Prestamo FROM Prestamos WHERE eliminado = 1
                )
            """)
            cursor.execute("DELETE FROM Prestamos WHERE eliminado = 1")
            conn.commit()
            return True, "Préstamos eliminados permanentemente."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {e}"
        finally:
            conn.close()

    @staticmethod
    def eliminar_definitivo_uno(id_prestamo):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM Recibos WHERE id_Prestamo = ?",
                           (id_prestamo,))
            cursor.execute("DELETE FROM PrestamoDetalle WHERE id_Prestamo = ?",
                           (id_prestamo,))
            cursor.execute("DELETE FROM Prestamos WHERE id_Prestamo = ?",
                           (id_prestamo,))
            conn.commit()
            return True, "Préstamo eliminado permanentemente."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {e}"
        finally:
            conn.close()

    def realizar_prestamo(self, id_ejemplar):
        ejemplar = Ejemplar.obtener_por_id(id_ejemplar)
        if not ejemplar or ejemplar.estado != 'Disponible':
            return False, "El ejemplar no está disponible."

        conn = get_connection()
        cursor = conn.cursor()

        try:
            fecha_dev = self.fecha_devolucion_esperada or \
                (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

            cursor.execute("""
                INSERT INTO Prestamos (id_Usuario, id_Ejemplar,
                                       fecha_Solicitud, fecha_Devolucion,
                                       estado, eliminado)
                OUTPUT INSERTED.id_Prestamo
                VALUES (?, ?, CAST(GETDATE() AS DATE), ?, 'activo', 0)
            """, (self.id_usuario, id_ejemplar, fecha_dev))

            fila = cursor.fetchone()
            if fila is None or fila[0] is None:
                conn.rollback()
                return False, "No se pudo obtener el ID del préstamo."

            self.id_prestamo = int(fila[0])

            cursor.execute("""
                INSERT INTO PrestamoDetalle (id_Prestamo, id_Libro)
                VALUES (?, ?)
            """, (self.id_prestamo, ejemplar.id_libro))

            cursor.execute("""
                UPDATE Ejemplar SET estado = 'Prestado'
                WHERE id_ejemplar = ?
            """, (id_ejemplar,))

            conn.commit()
            return True, "Préstamo registrado exitosamente."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            conn.close()

    def devolver(self):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id_Ejemplar FROM Prestamos WHERE id_Prestamo = ?
            """, (self.id_prestamo,))
            fila = cursor.fetchone()
            if fila and fila[0]:
                cursor.execute("""
                    UPDATE Ejemplar SET estado = 'Disponible'
                    WHERE id_ejemplar = ?
                """, (fila[0],))

            cursor.execute("""
                UPDATE Prestamos SET estado = 'devuelto'
                WHERE id_Prestamo = ?
            """, (self.id_prestamo,))

            conn.commit()
            return True, "Libro devuelto exitosamente."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            conn.close()

    def marcar_vencido(self):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE Prestamos SET estado = 'vencido'
                WHERE id_Prestamo = ?
            """, (self.id_prestamo,))
            conn.commit()
            return True, "Préstamo marcado como vencido."
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            conn.close()

    def obtener_detalle(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pd.id_Detalle, pd.id_Prestamo, pd.id_Libro,
                   l.Titulo AS titulo_libro
            FROM PrestamoDetalle pd
            JOIN Libros l ON pd.id_Libro = l.id_libro
            WHERE pd.id_Prestamo = ?
        """, (self.id_prestamo,))
        filas = cursor.fetchall()
        conn.close()
        return [
            {"id_Detalle": f[0], "id_Prestamo": f[1],
             "id_Libro": f[2], "titulo_libro": f[3]}
            for f in filas
        ]


class Comentario:
    @staticmethod
    def crear(id_usuario, id_libro, calificacion, comentario):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Comentarios (id_usuario, id_libro, calificacion, comentario)
                VALUES (?, ?, ?, ?)
            """, (id_usuario, id_libro, calificacion, comentario))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def obtener_por_libro(id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.calificacion, c.comentario, c.fecha, u.usuario_login
            FROM Comentarios c
            JOIN Usuario u ON c.id_usuario = u.id_usuario
            WHERE c.id_libro = ?
            ORDER BY c.fecha DESC
        """, (id_libro,))
        filas = cursor.fetchall()
        conn.close()
        return [
            {"calificacion": f[0], "comentario": f[1],
             "fecha": str(f[2]), "usuario": f[3]}
            for f in filas
        ]

    @staticmethod
    def ya_comento(id_usuario, id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM Comentarios
            WHERE id_usuario = ? AND id_libro = ?
        """, (id_usuario, id_libro))
        total = cursor.fetchone()[0]
        conn.close()
        return total > 0

    @staticmethod
    def usuario_leyo_libro(id_usuario, id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM Prestamos p
            JOIN PrestamoDetalle pd ON p.id_Prestamo = pd.id_Prestamo
            WHERE p.id_Usuario = ? AND pd.id_Libro = ?
        """, (id_usuario, id_libro))
        total = cursor.fetchone()[0]
        conn.close()
        return total > 0

    @staticmethod
    def obtener_mis_comentarios(id_usuario):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id_comentario, c.id_libro, c.calificacion, c.comentario,
                   c.fecha, l.Titulo
            FROM Comentarios c
            JOIN Libros l ON c.id_libro = l.id_libro
            WHERE c.id_usuario = ?
            ORDER BY c.fecha DESC
        """, (id_usuario,))
        filas = cursor.fetchall()
        conn.close()
        return [
            {"id_comentario": f[0], "id_libro": f[1], "calificacion": f[2],
             "comentario": f[3], "fecha": str(f[4]), "titulo": f[5]}
            for f in filas
        ]

    @staticmethod
    def obtener_todos():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id_comentario, c.id_libro, c.calificacion, c.comentario,
                   c.fecha, l.Titulo, u.usuario_login
            FROM Comentarios c
            JOIN Libros l ON c.id_libro = l.id_libro
            JOIN Usuario u ON c.id_usuario = u.id_usuario
            ORDER BY c.fecha DESC
        """)
        filas = cursor.fetchall()
        conn.close()
        return [
            {"id_comentario": f[0], "id_libro": f[1], "calificacion": f[2],
             "comentario": f[3], "fecha": str(f[4]), "titulo": f[5],
             "usuario": f[6]}
            for f in filas
        ]

    @staticmethod
    def promedio_libro(id_libro):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT AVG(CAST(calificacion AS FLOAT)), COUNT(*)
            FROM Comentarios
            WHERE id_libro = ?
        """, (id_libro,))
        fila = cursor.fetchone()
        conn.close()
        if fila and fila[0]:
            return round(fila[0], 1), fila[1]
        return 0, 0

    @staticmethod
    def libros_para_comentar(id_usuario):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT l.id_libro, l.Titulo, l.Autor, l.Imagen_URL
            FROM Prestamos p
            JOIN PrestamoDetalle pd ON p.id_Prestamo = pd.id_Prestamo
            JOIN Libros l ON pd.id_Libro = l.id_libro
            WHERE p.id_Usuario = ?
            AND l.id_libro NOT IN (
                SELECT id_libro FROM Comentarios WHERE id_usuario = ?
            )
        """, (id_usuario, id_usuario))
        filas = cursor.fetchall()
        conn.close()
        return [
            {"id_libro": f[0], "titulo": f[1], "autor": f[2], "imagen": f[3]}
            for f in filas
        ]