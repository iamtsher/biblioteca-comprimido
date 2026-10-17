import os
import ctypes


class AuthManager:
    """Gestor central de sesión y vistas. Patrón Singleton."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.usuario_actual = None
            cls._instance.container = None
            cls._instance.vistas = {}
            cls._instance.vistas_lazy = {}
        return cls._instance

    # ============================================================
    # CONTENEDOR
    # ============================================================
    def set_container(self, container_frame):
        self.container = container_frame

    # ============================================================
    # LOGIN / LOGOUT
    # ============================================================
    def login(self, usuario_login, password):
        from models import Usuario
        usuario = Usuario.verificar_login(usuario_login, password)
        if usuario:
            self.usuario_actual = usuario
            return True, f"Bienvenido, {usuario.usuario_login}!"
        return False, "Usuario o contraseña incorrectos."

    def logout(self):
        """Cierra sesión y destruye todas las vistas excepto login."""
        self.usuario_actual = None
        for nombre in list(self.vistas.keys()):
            if nombre != "login":
                try:
                    self.vistas[nombre].destroy()
                except Exception:
                    pass
                del self.vistas[nombre]

    def esta_autenticado(self):
        return self.usuario_actual is not None

    def es_admin(self):
        if self.usuario_actual and hasattr(self.usuario_actual, 'rol'):
            return self.usuario_actual.rol == 'Admin'
        return False

    def es_usuario_normal(self):
        return not self.es_admin()

    # ============================================================
    # REGISTRO DE VISTAS
    # ============================================================
    def registrar_vista(self, nombre, vista_frame):
        self.vistas[nombre] = vista_frame
        vista_frame.pack(fill="both", expand=True)
        vista_frame.pack_forget()

    def registrar_vista_lazy(self, nombre, factory_func):
        self.vistas_lazy[nombre] = factory_func

    def _crear_vista_lazy(self, nombre):
        if nombre in self.vistas_lazy and nombre not in self.vistas:
            vista = self.vistas_lazy[nombre](self.container)
            self.vistas[nombre] = vista
            vista.pack(fill="both", expand=True)
            vista.pack_forget()

    # ============================================================
    # MOSTRAR VISTA
    # ============================================================
    def mostrar_vista(self, nombre_vista):
        # El dashboard se recrea cada vez para reflejar cambios de rol
        if nombre_vista == "dashboard" and "dashboard" in self.vistas:
            try:
                self.vistas["dashboard"].destroy()
            except Exception:
                pass
            del self.vistas["dashboard"]

        if nombre_vista not in self.vistas and nombre_vista in self.vistas_lazy:
            self._crear_vista_lazy(nombre_vista)

        if nombre_vista not in self.vistas:
            return False

        # Ocultar todas las vistas
        for nombre, vista in self.vistas.items():
            try:
                vista.pack_forget()
            except Exception:
                try:
                    vista.grid_remove()
                except Exception:
                    pass

        # Mostrar la vista solicitada
        try:
            self.vistas[nombre_vista].pack(fill="both", expand=True)
            if hasattr(self.vistas[nombre_vista], 'on_show'):
                self.vistas[nombre_vista].on_show()
        except Exception:
            return False

        return True

    # ============================================================
    # UTILIDADES
    # ============================================================
    def get_usuario_actual(self):
        return self.usuario_actual

    def reiniciar_sesion(self):
        """Reinicia la sesión y vuelve al login."""
        self.usuario_actual = None
        try:
            root = self.container.winfo_toplevel()
            if hasattr(root, 'mostrar_login'):
                root.mostrar_login()
                return True
        except Exception:
            pass
        return False


# ============================================================
# UTILIDAD: Quitar botón X de una Toplevel (mantener min/max)
# ============================================================
def quitar_boton_cerrar(ventana):
    """Quita el botón X (cerrar) de una Toplevel."""
    try:
        ventana.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())

        GWL_STYLE = -16
        WS_SYSMENU = 0x00080000
        WS_MINIMIZEBOX = 0x00020000
        WS_MAXIMIZEBOX = 0x00010000

        estilo = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        estilo &= ~WS_SYSMENU
        estilo |= WS_MINIMIZEBOX
        estilo |= WS_MAXIMIZEBOX
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, estilo)

        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )
    except Exception:
        pass


# ============================================================
# UTILIDAD: Ruta del logo del proyecto
# ============================================================
def obtener_ruta_logo():
    """Devuelve la ruta del logo del proyecto o None."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rutas = [
        os.path.join(base_dir, "logo_unai.png"),
        os.path.join(base_dir, "logo_unai.jpeg"),
        os.path.join(base_dir, "logo_unai.jpg"),
    ]
    for ruta in rutas:
        if os.path.exists(ruta):
            return ruta
    return None


# ============================================================
# UTILIDAD: Generar PDF de reporte
# ============================================================
def generar_pdf_reporte(titulo_reporte, columnas, filas,
                        resumen=None, nombre_archivo="reporte.pdf"):
    """Genera un PDF con logo, título, tabla y resumen opcional."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib.utils import ImageReader
        from datetime import datetime

        carpeta = os.path.join(os.path.expanduser("~"),
                               "Documents", "ReportesBiblioteca")
        os.makedirs(carpeta, exist_ok=True)
        ruta_pdf = os.path.join(carpeta, nombre_archivo)

        c = pdf_canvas.Canvas(ruta_pdf, pagesize=letter)
        ancho, alto = letter

        # Encabezado
        c.setFillColorRGB(0.06, 0.09, 0.16)
        c.rect(0, alto - 110, ancho, 110, fill=True, stroke=False)

        x_texto = 50
        ruta_logo = obtener_ruta_logo()
        if ruta_logo:
            try:
                logo = ImageReader(ruta_logo)
                c.drawImage(logo, 50, alto - 95, width=70, height=70,
                            preserveAspectRatio=True, mask='auto')
                x_texto = 135
            except Exception:
                pass

        c.setFillColorRGB(0.22, 0.74, 0.97)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(x_texto, alto - 50, "BIBLIOTECA UNI")

        c.setFillColorRGB(0.58, 0.64, 0.69)
        c.setFont("Helvetica", 10)
        c.drawString(x_texto, alto - 70, "Sistema de Gestión Bibliotecaria")

        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(x_texto, alto - 95, titulo_reporte)

        c.setFillColorRGB(0.39, 0.45, 0.53)
        c.setFont("Helvetica", 9)
        c.drawRightString(ancho - 50, alto - 130,
                          f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        c.setStrokeColorRGB(0.88, 0.91, 0.94)
        c.line(50, alto - 150, ancho - 50, alto - 150)

        y = alto - 180

        c.setFillColorRGB(0.06, 0.09, 0.16)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"Total de registros: {len(filas)}")
        y -= 30

        if not filas:
            c.setFillColorRGB(0.58, 0.64, 0.69)
            c.setFont("Helvetica-Oblique", 11)
            c.drawCentredString(ancho / 2, alto / 2,
                                "No hay registros para mostrar")
            c.save()
            return ruta_pdf

        # Anchos proporcionales según número de columnas
        ancho_tabla = ancho - 100
        num_cols = len(columnas)

        proporciones_por_cols = {
            4: [0.10, 0.45, 0.30, 0.15],
            5: [0.08, 0.35, 0.25, 0.12, 0.20],
            6: [0.07, 0.20, 0.15, 0.15, 0.18, 0.25],
        }
        proporciones = proporciones_por_cols.get(
            num_cols, [1.0 / num_cols] * num_cols
        )
        anchos = [ancho_tabla * p for p in proporciones]

        altura_fila = 22
        c.setFillColorRGB(0.06, 0.09, 0.16)
        c.rect(50, y - altura_fila, ancho_tabla, altura_fila,
               fill=True, stroke=False)

        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 9)

        x = 55
        for i, col in enumerate(columnas):
            c.drawString(x, y - 15, str(col)[:20])
            x += anchos[i]

        y -= altura_fila
        c.setFont("Helvetica", 9)
        max_filas_por_pagina = 25

        for idx, fila in enumerate(filas):
            # Salto de página
            if idx > 0 and idx % max_filas_por_pagina == 0:
                c.showPage()
                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.rect(0, alto - 80, ancho, 80, fill=True, stroke=False)

                c.setFillColorRGB(0.22, 0.74, 0.97)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, alto - 50, f"BIBLIOTECA UNI - {titulo_reporte}")

                c.setFillColorRGB(0.39, 0.45, 0.53)
                c.setFont("Helvetica", 8)
                c.drawRightString(ancho - 50, alto - 65,
                                  f"Página {idx // max_filas_por_pagina + 1}")

                y = alto - 110
                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.rect(50, y - altura_fila, ancho_tabla, altura_fila,
                       fill=True, stroke=False)

                c.setFillColorRGB(1, 1, 1)
                c.setFont("Helvetica-Bold", 9)
                x = 55
                for i, col in enumerate(columnas):
                    c.drawString(x, y - 15, str(col)[:20])
                    x += anchos[i]
                y -= altura_fila
                c.setFont("Helvetica", 9)

            # Fila alterna
            if idx % 2 == 0:
                c.setFillColorRGB(0.97, 0.98, 0.99)
                c.rect(50, y - altura_fila, ancho_tabla, altura_fila,
                       fill=True, stroke=False)

            c.setFillColorRGB(0.06, 0.09, 0.16)
            x = 55
            for i, valor in enumerate(fila):
                texto = str(valor) if valor is not None else "—"
                max_chars = int(anchos[i] / 5.5)
                if len(texto) > max_chars:
                    texto = texto[:max_chars - 1] + "…"
                c.drawString(x, y - 15, texto)
                x += anchos[i]

            y -= altura_fila

        # Resumen final
        if resumen:
            y -= 20
            if y < 150:
                c.showPage()
                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.rect(0, alto - 80, ancho, 80, fill=True, stroke=False)
                c.setFillColorRGB(0.22, 0.74, 0.97)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, alto - 50, f"BIBLIOTECA UNI - {titulo_reporte}")
                y = alto - 120

            c.setFillColorRGB(0.06, 0.09, 0.16)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "RESUMEN")
            y -= 25

            for etiqueta, valor in resumen:
                c.setFillColorRGB(0.97, 0.98, 0.99)
                c.rect(50, y - 20, ancho - 100, 22, fill=True, stroke=False)

                c.setFillColorRGB(0.39, 0.45, 0.53)
                c.setFont("Helvetica", 10)
                c.drawString(65, y - 13, etiqueta)

                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.setFont("Helvetica-Bold", 11)
                c.drawRightString(ancho - 65, y - 13, str(valor))

                y -= 28

        c.setFillColorRGB(0.58, 0.64, 0.69)
        c.setFont("Helvetica", 8)
        c.drawCentredString(ancho / 2, 50,
                            "Documento generado automáticamente por el Sistema de Biblioteca UNI")

        c.save()
        return ruta_pdf

    except ImportError:
        raise ImportError(
            "Falta instalar 'reportlab':\n\npip install reportlab"
        )
    except Exception as e:
        raise Exception(f"No se pudo generar el PDF: {e}")