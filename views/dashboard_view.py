import os
import io
import urllib.request
import threading
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

from auth_manager import AuthManager, quitar_boton_cerrar
from models import Prestamo, Libro, Ejemplar, Usuario, Comentario
from database import get_connection
from views.libros_view import LibrosView
from views.ejemplares_view import EjemplaresView
from views.usuarios_view import UsuariosView
from views.prestamos_view import PrestamosView
from views.perfil_view import PerfilView

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.patches import Circle
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False


class DashboardView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f1f5f9")
        self.auth = AuthManager()
        self.botones_menu = {}
        self.vista_actual = None
        self.logo_sidebar = None
        self._build_ui()
        self._actualizar_reloj()
        self._verificar_notificaciones()

    def _build_ui(self):
        main = tk.Frame(self, bg="#f1f5f9")
        main.pack(fill="both", expand=True)
        self._construir_sidebar(main)
        self._construir_zona_derecha(main)

    def _construir_sidebar(self, parent):
        self.sidebar = tk.Frame(parent, bg="#0f172a", width=290)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo_frame = tk.Frame(self.sidebar, bg="#0f172a")
        logo_frame.pack(fill="x", pady=(25, 10), padx=20)

        self.logo_sidebar = self._cargar_logo_sidebar()
        if self.logo_sidebar:
            tk.Label(logo_frame, image=self.logo_sidebar,
                     bg="#0f172a").pack(side="left")
        else:
            tk.Label(logo_frame, text="📚",
                     font=("Segoe UI Emoji", 22),
                     bg="#0f172a", fg="#38bdf8").pack(side="left")

        tk.Label(logo_frame, text="Biblioteca",
                 font=("Segoe UI", 16, "bold"),
                 bg="#0f172a", fg="#f1f5f9").pack(side="left", padx=(10, 0))

        tk.Label(self.sidebar, text="UNI",
                 font=("Segoe UI", 9),
                 bg="#0f172a", fg="#64748b").pack(anchor="w", padx=75, pady=(0, 25))

        user_card = tk.Frame(self.sidebar, bg="#1e293b", padx=15, pady=12, cursor="hand2")
        user_card.pack(fill="x", padx=15, pady=(0, 20))

        rol_texto = "Administrador" if self.auth.es_admin() else "Usuario"
        lbl_rol = tk.Label(user_card, text=rol_texto,
                           font=("Segoe UI", 9),
                           bg="#1e293b", fg="#38bdf8")
        lbl_rol.pack(anchor="w")

        u = self.auth.get_usuario_actual()
        lbl_user = None
        if u:
            lbl_user = tk.Label(user_card, text=u.usuario_login,
                                font=("Segoe UI", 11, "bold"),
                                bg="#1e293b", fg="#f1f5f9")
            lbl_user.pack(anchor="w", pady=(2, 0))

            def on_enter(e):
                user_card.config(bg="#334155")
                lbl_rol.config(bg="#334155")
                lbl_user.config(bg="#334155")

            def on_leave(e):
                user_card.config(bg="#1e293b")
                lbl_rol.config(bg="#1e293b")
                lbl_user.config(bg="#1e293b")

            def on_click(e):
                self.abrir_perfil_ventana()

            for w in [user_card, lbl_rol, lbl_user]:
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
                w.bind("<Button-1>", on_click)

        tk.Frame(self.sidebar, bg="#334155", height=1).pack(fill="x", padx=15, pady=(0, 15))

        tk.Label(self.sidebar, text="MENÚ PRINCIPAL",
                 font=("Segoe UI", 8, "bold"),
                 bg="#0f172a", fg="#64748b").pack(anchor="w", padx=25, pady=(0, 10))

        opciones = [
            ("home", "", "Inicio"),
            ("libros", "", "Libros"),
            ("ejemplares", "", "Ejemplares"),
            ("prestamos", "", "Préstamos"),
        ]
        if self.auth.es_admin():
            opciones.append(("usuarios", "", "Usuarios"))
        opciones.append(("stats", "", "Estadísticas"))

        for key, icono, texto in opciones:
            self.botones_menu[key] = self._crear_boton_menu(key, icono, texto)

        logout_frame = tk.Frame(self.sidebar, bg="#0f172a")
        logout_frame.pack(side="bottom", fill="x", pady=20, padx=15)

        tk.Button(logout_frame, text="Cerrar Sesión",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", pady=10,
                  command=self._logout).pack(fill="x")

    def abrir_perfil_ventana(self):
        w = tk.Toplevel(self)
        w.title("Mi Perfil")
        w.geometry("500x520")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Mi Perfil",
                 font=("Segoe UI", 16, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=25, pady=18)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=18, pady=6,
                  command=w.destroy).pack(side="right", padx=25, pady=15)

        perfil = PerfilView(w)
        perfil.pack(fill="both", expand=True)
        perfil.on_show()

    def _construir_zona_derecha(self, parent):
        zona_derecha = tk.Frame(parent, bg="#f1f5f9")
        zona_derecha.pack(side="right", fill="both", expand=True)

        topbar = tk.Frame(zona_derecha, bg="white", height=110)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        info_frame = tk.Frame(topbar, bg="white")
        info_frame.pack(side="left", padx=40, pady=8)

        u = self.auth.get_usuario_actual()
        saludo = f"Hola, {u.usuario_login}" if u else "Hola"

        tk.Label(info_frame, text=saludo,
                 font=("Segoe UI", 11),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(14, 0))

        self.lbl_titulo_seccion = tk.Label(
            info_frame, text="Inicio",
            font=("Segoe UI", 24, "bold"),
            bg="white", fg="#0f172a")
        self.lbl_titulo_seccion.pack(anchor="w", pady=(2, 10))

        derecha = tk.Frame(topbar, bg="white")
        derecha.pack(side="right", padx=40, pady=30)

        tk.Button(derecha, text="Cerrar Sistema",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=18, pady=10,
                  command=self._cerrar_sistema).pack(side="right")

        tk.Frame(derecha, bg="#e2e8f0", width=1, height=40).pack(side="right", padx=20)

        reloj_frame = tk.Frame(derecha, bg="white")
        reloj_frame.pack(side="right")

        self.lbl_reloj = tk.Label(reloj_frame, text="",
                                  font=("Segoe UI", 11, "bold"),
                                  bg="white", fg="#0f172a")
        self.lbl_reloj.pack(side="left")

        tk.Frame(derecha, bg="#e2e8f0", width=1, height=40).pack(side="right", padx=20)

        notif_frame = tk.Frame(derecha, bg="white")
        notif_frame.pack(side="right")

        self.btn_notif = tk.Button(
            notif_frame, text="🔔",
            font=("Segoe UI Emoji", 16),
            bg="white", fg="#0f172a",
            bd=0, cursor="hand2",
            activebackground="#f1f5f9", relief="flat",
            padx=10, pady=6,
            command=self._mostrar_notificaciones)
        self.btn_notif.pack()

        self.lbl_badge = tk.Label(notif_frame, text="",
                                  font=("Segoe UI", 8, "bold"),
                                  bg="#ef4444", fg="white",
                                  padx=5, pady=1)

        tk.Frame(zona_derecha, bg="#e2e8f0", height=1).pack(fill="x")

        self.vista_container = tk.Frame(zona_derecha, bg="#f1f5f9")
        self.vista_container.pack(fill="both", expand=True)
        self.vista_container.grid_rowconfigure(0, weight=1)
        self.vista_container.grid_columnconfigure(0, weight=1)

        self.vistas = {
            "home": self._crear_vista_home(),
            "libros": LibrosView(self.vista_container),
            "ejemplares": EjemplaresView(self.vista_container),
            "prestamos": PrestamosView(self.vista_container),
            "stats": self._crear_vista_stats(),
        }
        if self.auth.es_admin():
            self.vistas["usuarios"] = UsuariosView(self.vista_container)

        for v in self.vistas.values():
            v.grid(row=0, column=0, sticky="nsew")
            v.grid_remove()

        self.mostrar_vista("home")

    def _cargar_logo_sidebar(self):
        if not PIL_OK:
            return None
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rutas = [
                os.path.join(base_dir, "logo_unai.png"),
                os.path.join(base_dir, "logo_unai.jpeg"),
                os.path.join(base_dir, "logo_unai.jpg"),
            ]
            ruta_logo = next((r for r in rutas if os.path.exists(r)), None)
            if not ruta_logo:
                return None

            img = Image.open(ruta_logo).convert("RGBA")
            img.thumbnail((40, 40), Image.LANCZOS)

            padding = 6
            card = Image.new(
                "RGBA",
                (img.width + padding * 2, img.height + padding * 2),
                (0, 0, 0, 0)
            )
            draw = ImageDraw.Draw(card)
            draw.rounded_rectangle(
                (0, 0, img.width + padding * 2, img.height + padding * 2),
                radius=8,
                fill=(255, 255, 255, 255)
            )
            card.paste(img, (padding, padding),
                       img if img.mode == "RGBA" else None)
            return ImageTk.PhotoImage(card)
        except Exception:
            return None

    def _crear_vista_home(self):
        frame = tk.Frame(self.vista_container, bg="#f1f5f9")

        canvas = tk.Canvas(frame, bg="#f1f5f9", highlightthickness=0)

        def on_scroll_home(*args):
            canvas.yview(*args)
            canvas.update_idletasks()

        scroll = tk.Scrollbar(frame, orient="vertical", command=on_scroll_home)
        body = tk.Frame(canvas, bg="#f1f5f9")

        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        body.bind("<Configure>",
                  lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(
                        canvas.find_withtag("all")[0], width=e.width))
        canvas.bind("<MouseWheel>",
                    lambda e: (canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
                               canvas.update_idletasks()))

        self.frame_alerta = tk.Frame(body, bg="#fef2f2",
                                     highlightthickness=1,
                                     highlightbackground="#fecaca")

        self._construir_banner_home(body)
        self._construir_ocupacion_home(body)
        self._construir_accesos_rapidos(body)

        tk.Label(body, text="Préstamos próximos a vencer",
                 font=("Segoe UI", 13, "bold"),
                 bg="#f1f5f9", fg="#334155").pack(anchor="w", padx=30, pady=(15, 10))
        self.frame_proximos_vencer = tk.Frame(body, bg="white",
                                               highlightthickness=1,
                                               highlightbackground="#e2e8f0")
        self.frame_proximos_vencer.pack(fill="x", padx=25, pady=(0, 25))

        return frame

    def _construir_banner_home(self, body):
        banner = tk.Frame(body, bg="white", highlightthickness=1,
                          highlightbackground="#e2e8f0")
        banner.pack(fill="x", padx=25, pady=(20, 20))

        tk.Frame(banner, bg="#1e3a8a", height=5).pack(fill="x")

        inner_banner = tk.Frame(banner, bg="white", padx=35, pady=28)
        inner_banner.pack(fill="x")

        u = self.auth.get_usuario_actual()
        login = u.usuario_login if u else "usuario"
        hora = datetime.now().hour

        if hora < 12:
            saludo, icono_saludo = f"Buenos días, {login}", "🌅"
        elif hora < 19:
            saludo, icono_saludo = f"Buenas tardes, {login}", "☀️"
        else:
            saludo, icono_saludo = f"Buenas noches, {login}", "🌙"

        dias = ["Lunes", "Martes", "Miércoles", "Jueves",
                "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre",
                 "noviembre", "diciembre"]
        ahora = datetime.now()
        fecha_texto = (f"{dias[ahora.weekday()]}, {ahora.day} de "
                       f"{meses[ahora.month - 1]} de {ahora.year}")

        header_home = tk.Frame(inner_banner, bg="white")
        header_home.pack(fill="x")

        icono_frame = tk.Frame(header_home, bg="#1e3a8a", width=70, height=70)
        icono_frame.pack(side="left")
        icono_frame.pack_propagate(False)

        tk.Label(icono_frame, text=icono_saludo,
                 font=("Segoe UI Emoji", 32),
                 bg="#1e3a8a", fg="white").pack(expand=True)

        texto_frame = tk.Frame(header_home, bg="white")
        texto_frame.pack(side="left", padx=(20, 0), fill="x", expand=True)

        self.lbl_home_saludo = tk.Label(texto_frame, text=saludo,
                                        font=("Segoe UI", 22, "bold"),
                                        bg="white", fg="#0f172a")
        self.lbl_home_saludo.pack(anchor="w")

        self.lbl_home_fecha = tk.Label(texto_frame, text=fecha_texto,
                                       font=("Segoe UI", 11),
                                       bg="white", fg="#64748b")
        self.lbl_home_fecha.pack(anchor="w", pady=(3, 0))

        botones_banner = tk.Frame(header_home, bg="white")
        botones_banner.pack(side="right")

        tk.Button(botones_banner, text="Nuevo Préstamo",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1e3a8a", fg="white",
                  activebackground="#1e40af", activeforeground="white",
                  bd=0, cursor="hand2", padx=18, pady=10,
                  command=lambda: self._accion_rapida("prestamos_nuevo")
                  ).pack(side="left", padx=3)

        if self.auth.es_admin():
            tk.Button(botones_banner, text="Nuevo Libro",
                      font=("Segoe UI", 10, "bold"),
                      bg="#e2e8f0", fg="#0f172a",
                      activebackground="#cbd5e1", activeforeground="#0f172a",
                      bd=0, cursor="hand2", padx=18, pady=10,
                      command=lambda: self._accion_rapida("libros_nuevo")
                      ).pack(side="left", padx=3)

    def _construir_ocupacion_home(self, body):
        ocupacion_frame = tk.Frame(body, bg="white", highlightthickness=1,
                                   highlightbackground="#e2e8f0")
        ocupacion_frame.pack(fill="x", padx=25, pady=(0, 20))

        inner = tk.Frame(ocupacion_frame, bg="white", padx=25, pady=18)
        inner.pack(fill="x")

        tk.Label(inner, text="Ocupación de la biblioteca",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        barra_container = tk.Frame(inner, bg="white")
        barra_container.pack(fill="x", pady=(12, 5))

        self.barra_ocupacion_bg = tk.Frame(barra_container, bg="#e2e8f0", height=24)
        self.barra_ocupacion_bg.pack(fill="x")
        self.barra_ocupacion_bg.pack_propagate(False)

        self.barra_ocupacion = tk.Frame(self.barra_ocupacion_bg, bg="#10b981", height=24)
        self.barra_ocupacion.place(x=0, y=0, relwidth=0, relheight=1)

        self.lbl_ocupacion = tk.Label(inner, text="",
                                      font=("Segoe UI", 9),
                                      bg="white", fg="#64748b")
        self.lbl_ocupacion.pack(anchor="w")

    def _construir_accesos_rapidos(self, body):
        tk.Label(body, text="Accesos rápidos",
                 font=("Segoe UI", 13, "bold"),
                 bg="#f1f5f9", fg="#334155").pack(anchor="w", padx=30, pady=(15, 10))

        accesos_frame = tk.Frame(body, bg="#f1f5f9")
        accesos_frame.pack(fill="x", padx=25, pady=(0, 20))

        for i in range(4):
            accesos_frame.grid_columnconfigure(i, weight=1)

        self._crear_acceso_rapido(
            accesos_frame, 0, "📤", "Nuevo Préstamo",
            lambda: self._accion_rapida("prestamos_nuevo"))

        if self.auth.es_admin():
            self._crear_acceso_rapido(
                accesos_frame, 1, "📖", "Nuevo Libro",
                lambda: self._accion_rapida("libros_nuevo"))
            self._crear_acceso_rapido(
                accesos_frame, 2, "👤", "Nuevo Usuario",
                lambda: self._accion_rapida("usuarios_nuevo"))
        else:
            self._crear_acceso_rapido(
                accesos_frame, 1, "🔍", "Buscar Libro",
                lambda: self._accion_rapida("libros_buscar"))
            self._crear_acceso_rapido(
                accesos_frame, 2, "📜", "Historial",
                lambda: self._accion_rapida("prestamos_historial"))

        self._crear_acceso_rapido(
            accesos_frame, 3, "👤", "Mi Perfil",
            lambda: self.abrir_perfil_ventana())

    def _crear_acceso_rapido(self, parent, col, icono, texto, comando):
        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0", cursor="hand2")
        card.grid(row=0, column=col, padx=6, pady=6, sticky="nsew")

        inner = tk.Frame(card, bg="white", padx=15, pady=25)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=icono, font=("Segoe UI Emoji", 32),
                 bg="white", fg="#475569").pack()

        tk.Label(inner, text=texto,
                 font=("Segoe UI", 11),
                 bg="white", fg="#334155").pack(pady=(10, 0))

        def on_enter(e):
            card.config(highlightbackground="#94a3b8", highlightthickness=2)

        def on_leave(e):
            card.config(highlightbackground="#e2e8f0", highlightthickness=1)

        def on_click(e):
            comando()

        for w in [card, inner] + list(inner.winfo_children()):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    def _accion_rapida(self, accion):
        acciones = {
            "prestamos_nuevo": lambda: (
                self.mostrar_vista("prestamos"),
                self.after(200, lambda: self.vistas["prestamos"].nuevo())
            ),
            "libros_nuevo": lambda: (
                self.mostrar_vista("libros"),
                self.after(200, lambda: self.vistas["libros"].abrir_form())
            ),
            "libros_buscar": lambda: self.mostrar_vista("libros"),
            "usuarios_nuevo": lambda: (
                self.mostrar_vista("usuarios"),
                self.after(200, lambda: self.vistas["usuarios"].abrir_form())
            ),
            "prestamos_historial": lambda: (
                self.mostrar_vista("prestamos"),
                self.after(200, lambda: self.vistas["prestamos"].historial())
            ),
        }
        if accion in acciones:
            acciones[accion]()

    def _refrescar_home(self):
        try:
            self._refrescar_saludo()
            self._refrescar_ocupacion()
            self._refrescar_alerta()
            self._refrescar_proximos_vencer()
        except Exception:
            pass

    def _refrescar_saludo(self):
        u = self.auth.get_usuario_actual()
        login = u.usuario_login if u else "usuario"
        hora = datetime.now().hour

        if hora < 12:
            saludo = f"Buenos días, {login}"
        elif hora < 19:
            saludo = f"Buenas tardes, {login}"
        else:
            saludo = f"Buenas noches, {login}"

        self.lbl_home_saludo.config(text=saludo)

        dias = ["Lunes", "Martes", "Miércoles", "Jueves",
                "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre",
                 "noviembre", "diciembre"]
        ahora = datetime.now()
        fecha_texto = (f"{dias[ahora.weekday()]}, {ahora.day} de "
                       f"{meses[ahora.month - 1]} de {ahora.year}")
        self.lbl_home_fecha.config(text=fecha_texto)

    def _refrescar_ocupacion(self):
        total_ejemplares = Ejemplar.contar()
        disponibles = Ejemplar.contar_disponibles()
        prestados = total_ejemplares - disponibles

        if total_ejemplares > 0:
            porcentaje = int((prestados / total_ejemplares) * 100)
        else:
            porcentaje = 0

        if porcentaje < 30:
            color_barra = "#10b981"
        elif porcentaje < 70:
            color_barra = "#f59e0b"
        else:
            color_barra = "#ef4444"

        self.barra_ocupacion.config(bg=color_barra)
        self.barra_ocupacion.place(relwidth=porcentaje / 100)
        self.lbl_ocupacion.config(
            text=f"{prestados} prestados de {total_ejemplares} totales ({porcentaje}% ocupado)")

    def _refrescar_alerta(self):
        for w in self.frame_alerta.winfo_children():
            w.destroy()

        try:
            prestamos = Prestamo.obtener_activos()
            vencidos = []
            hoy = datetime.now().date()

            for p in prestamos:
                if p.fecha_devolucion_esperada:
                    try:
                        fecha_dev = datetime.strptime(
                            str(p.fecha_devolucion_esperada)[:10],
                            "%Y-%m-%d").date()
                        if fecha_dev < hoy:
                            vencidos.append(p)
                    except Exception:
                        pass
        except Exception:
            vencidos = []

        if not vencidos:
            self.frame_alerta.pack_forget()
            return

        if not self.frame_alerta.winfo_ismapped():
            self.frame_alerta.pack(fill="x", padx=25, pady=(20, 0),
                                   before=self.frame_alerta.master.winfo_children()[1])

        inner_alerta = tk.Frame(self.frame_alerta, bg="#fef2f2", padx=20, pady=15)
        inner_alerta.pack(fill="x")

        texto_alerta = tk.Frame(inner_alerta, bg="#fef2f2")
        texto_alerta.pack(side="left", fill="x", expand=True)

        tk.Label(texto_alerta,
                 text=f"¡Atención! Hay {len(vencidos)} préstamo(s) vencido(s)",
                 font=("Segoe UI", 11, "bold"),
                 bg="#fef2f2", fg="#991b1b",
                 anchor="w").pack(anchor="w")

        tk.Label(texto_alerta,
                 text="Revisa la sección de Préstamos para gestionar las devoluciones",
                 font=("Segoe UI", 9),
                 bg="#fef2f2", fg="#7f1d1d",
                 anchor="w").pack(anchor="w")

        tk.Button(inner_alerta, text="Ver Préstamos",
                  font=("Segoe UI", 10, "bold"),
                  bg="#dc2626", fg="white",
                  activebackground="#b91c1c", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=8,
                  command=lambda: self.mostrar_vista("prestamos")
                  ).pack(side="right")

    def _refrescar_proximos_vencer(self):
        for w in self.frame_proximos_vencer.winfo_children():
            w.destroy()

        es_admin = self.auth.es_admin()
        u = self.auth.get_usuario_actual()
        prestamos = Prestamo.obtener_activos()

        if not es_admin and u:
            prestamos = [p for p in prestamos
                         if p.nombre_usuario == u.usuario_login]

        hoy = datetime.now().date()
        proximos = []

        for p in prestamos:
            if p.fecha_devolucion_esperada:
                try:
                    fecha_dev = datetime.strptime(
                        str(p.fecha_devolucion_esperada)[:10],
                        "%Y-%m-%d").date()
                    dias = (fecha_dev - hoy).days
                    if 0 <= dias <= 7:
                        proximos.append((p, dias))
                except Exception:
                    pass

        proximos.sort(key=lambda x: x[1])

        if not proximos:
            tk.Label(self.frame_proximos_vencer,
                     text="No hay préstamos próximos a vencer esta semana",
                     font=("Segoe UI", 11),
                     bg="white", fg="#94a3b8").pack(pady=30)
            return

        for i, (p, dias) in enumerate(proximos[:8]):
            fila = tk.Frame(self.frame_proximos_vencer, bg="white",
                            padx=20, pady=10)
            fila.pack(fill="x")

            if dias == 0:
                color = "#ef4444"
                texto_dias = "Vence HOY"
            elif dias <= 3:
                color = "#f59e0b"
                texto_dias = f"Vence en {dias} días"
            else:
                color = "#3b82f6"
                texto_dias = f"Vence en {dias} días"

            info = tk.Frame(fila, bg="white")
            info.pack(side="left", fill="x", expand=True)

            tk.Label(info,
                     text=f"Préstamo #{p.id_prestamo} - {p.nombre_usuario}",
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#0f172a",
                     anchor="w").pack(anchor="w")

            fecha_dev = str(p.fecha_devolucion_esperada)[:10] if p.fecha_devolucion_esperada else "—"
            tk.Label(info,
                     text=f"{fecha_dev}  •  {texto_dias}",
                     font=("Segoe UI", 9),
                     bg="white", fg=color,
                     anchor="w").pack(anchor="w")

            if i < len(proximos[:8]) - 1:
                tk.Frame(self.frame_proximos_vencer, bg="#f1f5f9",
                         height=1).pack(fill="x", padx=20)

    def _crear_vista_stats(self):
        frame = tk.Frame(self.vista_container, bg="#f1f5f9")

        header = tk.Frame(frame, bg="#f1f5f9", height=55)
        header.pack(fill="x", padx=25, pady=(12, 0))
        header.pack_propagate(False)

        tk.Button(header, text="Exportar PDF",
                  font=("Segoe UI", 11, "bold"),
                  bg="#22c55e", fg="white",
                  activebackground="#16a34a", activeforeground="white",
                  bd=0, cursor="hand2", padx=22, pady=8,
                  command=self._exportar_stats_pdf).pack(side="right", pady=8)

        tk.Button(header, text="Actualizar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=22, pady=8,
                  command=self._refresh_stats).pack(side="right", padx=(0, 10), pady=8)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Stats.TNotebook",
                        background="#f1f5f9",
                        borderwidth=0)
        style.configure("Stats.TNotebook.Tab",
                        background="#e2e8f0",
                        foreground="#334155",
                        font=("Segoe UI", 10, "bold"),
                        padding=[18, 8])
        style.map("Stats.TNotebook.Tab",
                  background=[("selected", "#1e3a8a")],
                  foreground=[("selected", "white")])

        notebook = ttk.Notebook(frame, style="Stats.TNotebook")
        notebook.pack(fill="both", expand=True, padx=25, pady=(15, 15))

        tab_resumen = tk.Frame(notebook, bg="#f1f5f9")
        tab_ranking = tk.Frame(notebook, bg="#f1f5f9")
        tab_comentarios = tk.Frame(notebook, bg="#f1f5f9")

        notebook.add(tab_resumen, text="Resumen")
        notebook.add(tab_ranking, text="Ranking y Movimientos")
        notebook.add(tab_comentarios, text="Comentarios")

        canvas_resumen = tk.Canvas(tab_resumen, bg="#f1f5f9", highlightthickness=0)
        scroll_resumen = tk.Scrollbar(tab_resumen, orient="vertical",
                                      command=canvas_resumen.yview)
        canvas_resumen.configure(yscrollcommand=scroll_resumen.set)
        canvas_resumen.pack(side="left", fill="both", expand=True)
        scroll_resumen.pack(side="right", fill="y")

        body = tk.Frame(canvas_resumen, bg="#f1f5f9")
        body_window = canvas_resumen.create_window((0, 0), window=body, anchor="nw")

        body.bind("<Configure>",
                  lambda e: canvas_resumen.configure(
                      scrollregion=canvas_resumen.bbox("all")))
        canvas_resumen.bind(
            "<Configure>",
            lambda e: canvas_resumen.itemconfig(body_window, width=e.width))

        def _on_wheel(event):
            try:
                canvas_resumen.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        canvas_resumen.bind("<MouseWheel>", _on_wheel)
        body.bind("<MouseWheel>", _on_wheel)

        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        cards = tk.Frame(body, bg="#f1f5f9")
        cards.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 10))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1)

        self.card_libros = self._crear_card_stats(cards, "Libros", "0", "#3b82f6")
        self.card_libros.grid(row=0, column=0, padx=6, pady=5, sticky="nsew")

        self.card_ejemplares = self._crear_card_stats(cards, "Ejemplares", "0", "#8b5cf6")
        self.card_ejemplares.grid(row=0, column=1, padx=6, pady=5, sticky="nsew")

        self.card_disponibles = self._crear_card_stats(cards, "Disponibles", "0", "#10b981")
        self.card_disponibles.grid(row=0, column=2, padx=6, pady=5, sticky="nsew")

        es_admin = self.auth.es_admin()

        self.card_usuarios = None
        if es_admin:
            self.card_usuarios = self._crear_card_stats(cards, "Usuarios", "0", "#f59e0b")
            self.card_usuarios.grid(row=1, column=0, padx=6, pady=5, sticky="nsew")

        titulo_prestamos = "Préstamos activos" if es_admin else "Mis préstamos activos"
        self.card_prestamos = self._crear_card_stats(
            cards, titulo_prestamos, "0", "#ef4444")
        self.card_prestamos.grid(row=1, column=0 if not es_admin else 1,
                                 padx=6, pady=5, sticky="nsew")

        titulo_historial = "Históricos" if es_admin else "Mi historial"
        self.card_historial = self._crear_card_stats(
            cards, titulo_historial, "0", "#06b6d4")
        self.card_historial.grid(row=1, column=1 if not es_admin else 2,
                                 padx=6, pady=5, sticky="nsew")

        if MATPLOTLIB_OK:
            self.frame_pastel = tk.Frame(body, bg="white", highlightthickness=1,
                                         highlightbackground="#e2e8f0", height=210)
            self.frame_pastel.grid(row=2, column=0, padx=6, pady=5, sticky="nsew")
            self.frame_pastel.pack_propagate(False)

            self.frame_barras = tk.Frame(body, bg="white", highlightthickness=1,
                                         highlightbackground="#e2e8f0", height=210)
            self.frame_barras.grid(row=2, column=1, padx=6, pady=5, sticky="nsew")
            self.frame_barras.pack_propagate(False)
        else:
            tk.Label(body,
                     text="⚠️  Instala matplotlib:\n\npip install matplotlib",
                     font=("Segoe UI", 11), bg="#f1f5f9",
                     fg="#dc2626").grid(row=2, column=0, columnspan=2, pady=50)

        tk.Label(tab_ranking, text="Libro más prestado",
                 font=("Segoe UI", 13, "bold"),
                 bg="#f1f5f9", fg="#334155").pack(anchor="w", padx=25, pady=(15, 10))
        self.frame_top_libro_stats = tk.Frame(tab_ranking, bg="white",
                                              highlightthickness=1,
                                              highlightbackground="#e2e8f0")
        self.frame_top_libro_stats.pack(fill="x", padx=25, pady=(0, 20))

        tk.Label(tab_ranking, text="Últimos movimientos",
                 font=("Segoe UI", 13, "bold"),
                 bg="#f1f5f9", fg="#334155").pack(anchor="w", padx=25, pady=(15, 10))
        self.frame_movimientos_stats = tk.Frame(tab_ranking, bg="white",
                                                highlightthickness=1,
                                                highlightbackground="#e2e8f0")
        self.frame_movimientos_stats.pack(fill="x", padx=25, pady=(0, 20))

        tk.Label(tab_comentarios, text="Comentarios",
                 font=("Segoe UI", 13, "bold"),
                 bg="#f1f5f9", fg="#334155").pack(anchor="w", padx=25, pady=(15, 10))
        self.frame_comentarios = tk.Frame(tab_comentarios, bg="white",
                                          highlightthickness=1,
                                          highlightbackground="#e2e8f0")
        self.frame_comentarios.pack(fill="x", padx=25, pady=(0, 20))

        self.lbl_actualizado = tk.Label(frame, text="",
                                        font=("Segoe UI", 9),
                                        bg="#f1f5f9", fg="#94a3b8")
        self.lbl_actualizado.pack(pady=(0, 10))

        return frame

    def _crear_card_stats(self, parent, titulo, valor, color):
        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        tk.Frame(card, bg=color, height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(inner, text=titulo,
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b").pack(anchor="w")

        lbl_valor = tk.Label(inner, text=valor,
                             font=("Segoe UI", 22, "bold"),
                             bg="white", fg=color)
        lbl_valor.pack(anchor="w", pady=(2, 0))

        card.lbl_valor = lbl_valor
        return card

    def _refresh_stats(self):
        try:
            es_admin = self.auth.es_admin()
            u_actual = self.auth.get_usuario_actual()

            total_libros = Libro.contar()
            total_ejemplares = Ejemplar.contar()
            disponibles = Ejemplar.contar_disponibles()

            self.card_libros.lbl_valor.config(text=f"{total_libros:,}")
            self.card_ejemplares.lbl_valor.config(text=f"{total_ejemplares:,}")
            self.card_disponibles.lbl_valor.config(text=f"{disponibles:,}")

            if es_admin:
                total_usuarios = Usuario.contar()
                prestamos_activos = Prestamo.contar_activos()
                historial = Prestamo.contar_historial()

                if self.card_usuarios:
                    self.card_usuarios.lbl_valor.config(text=f"{total_usuarios:,}")
                self.card_prestamos.lbl_valor.config(text=f"{prestamos_activos:,}")
                self.card_historial.lbl_valor.config(text=f"{historial:,}")
            else:
                prestamos_usuario = Prestamo.obtener_activos()
                historial_usuario = Prestamo.obtener_historial()

                if u_actual:
                    prestamos_usuario = [p for p in prestamos_usuario
                                         if p.nombre_usuario == u_actual.usuario_login]
                    historial_usuario = [h for h in historial_usuario
                                         if h.nombre_usuario == u_actual.usuario_login]

                self.card_prestamos.lbl_valor.config(text=f"{len(prestamos_usuario):,}")
                self.card_historial.lbl_valor.config(text=f"{len(historial_usuario):,}")

            self.lbl_actualizado.config(
                text=f"Última actualización: "
                     f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

            if MATPLOTLIB_OK:
                self._dibujar_graficos(disponibles, total_ejemplares - disponibles)

            self._refrescar_top_libro_stats()
            self._refrescar_movimientos_stats()
            self._refrescar_comentarios_stats()
        except Exception:
            pass

    def _refrescar_top_libro_stats(self):
        for w in self.frame_top_libro_stats.winfo_children():
            w.destroy()

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 l.id_libro, l.Titulo, l.Autor, l.Imagen_URL,
                       COUNT(pd.id_Detalle) AS Total
                FROM Libros l
                INNER JOIN PrestamoDetalle pd ON l.id_libro = pd.id_Libro
                GROUP BY l.id_libro, l.Titulo, l.Autor, l.Imagen_URL
                ORDER BY Total DESC, l.Titulo
            """)
            fila = cursor.fetchone()
            conn.close()
        except Exception:
            fila = None

        card = tk.Frame(self.frame_top_libro_stats, bg="white",
                        highlightthickness=1, highlightbackground="#e2e8f0")
        card.pack(fill="x")

        tk.Frame(card, bg="#f59e0b", height=4).pack(fill="x")

        inner_top = tk.Frame(card, bg="white", padx=25, pady=18)
        inner_top.pack(fill="x")

        if not fila:
            icono_frame = tk.Frame(inner_top, bg="#f1f5f9", width=60, height=80)
            icono_frame.pack(side="left")
            icono_frame.pack_propagate(False)

            tk.Label(icono_frame, text="📖",
                     font=("Segoe UI Emoji", 26),
                     bg="#f1f5f9", fg="#94a3b8").pack(expand=True)

            info_top = tk.Frame(inner_top, bg="white")
            info_top.pack(side="left", padx=(18, 0), fill="x", expand=True)

            tk.Label(info_top, text="Aún no hay préstamos registrados",
                     font=("Segoe UI", 12, "bold"),
                     bg="white", fg="#94a3b8",
                     anchor="w").pack(anchor="w")

            tk.Label(info_top, text="Cuando alguien pida un libro, aparecerá aquí",
                     font=("Segoe UI", 10),
                     bg="white", fg="#cbd5e1",
                     anchor="w").pack(anchor="w", pady=(3, 0))
            return

        id_libro, titulo_libro, autor_libro, imagen_url, total_prestamos = fila

        # ---------- Foto del libro ----------
        foto_frame = tk.Frame(inner_top, bg="#f1f5f9", width=60, height=80,
                              highlightthickness=1, highlightbackground="#e2e8f0")
        foto_frame.pack(side="left")
        foto_frame.pack_propagate(False)

        lbl_foto = tk.Label(foto_frame, text="📖",
                            font=("Segoe UI Emoji", 22),
                            bg="#f1f5f9", fg="#94a3b8")
        lbl_foto.pack(expand=True)

        if PIL_OK and imagen_url:
            def cargar_en_thread():
                try:
                    req = urllib.request.Request(
                        imagen_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        data = resp.read()

                    img = Image.open(io.BytesIO(data))
                    if img.size[0] < 20 or img.size[1] < 20:
                        return

                    img.thumbnail((60, 80), Image.LANCZOS)

                    def aplicar():
                        try:
                            if not lbl_foto.winfo_exists():
                                return
                            photo = ImageTk.PhotoImage(img)
                            lbl_foto.config(image=photo, text="")
                            lbl_foto.image = photo
                        except Exception:
                            pass

                    self.after(0, aplicar)
                except Exception:
                    pass

            threading.Thread(target=cargar_en_thread, daemon=True).start()

        # ---------- Info ----------
        info_top = tk.Frame(inner_top, bg="white")
        info_top.pack(side="left", padx=(18, 0), fill="x", expand=True)

        tk.Label(info_top, text=titulo_libro,
                 font=("Segoe UI", 14, "bold"),
                 bg="white", fg="#0f172a",
                 anchor="w").pack(anchor="w")

        tk.Label(info_top, text=autor_libro or "Autor desconocido",
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b",
                 anchor="w").pack(anchor="w", pady=(3, 0))

        # ---------- Badge ----------
        badge = tk.Frame(inner_top, bg="#fef3c7",
                         highlightthickness=1, highlightbackground="#fcd34d")
        badge.pack(side="right", padx=(10, 0))

        tk.Label(badge, text=f"{total_prestamos}",
                 font=("Segoe UI", 16, "bold"),
                 bg="#fef3c7", fg="#92400e",
                 padx=(12, 4), pady=10).pack(side="left")

        tk.Label(badge, text="préstamos",
                 font=("Segoe UI", 9),
                 bg="#fef3c7", fg="#92400e",
                 padx=(0, 12)).pack(side="left")

    def _refrescar_movimientos_stats(self):
        for w in self.frame_movimientos_stats.winfo_children():
            w.destroy()

        es_admin = self.auth.es_admin()
        u = self.auth.get_usuario_actual()
        prestamos = Prestamo.obtener_historial()

        if not es_admin and u:
            prestamos = [p for p in prestamos
                         if p.nombre_usuario == u.usuario_login]

        prestamos = prestamos[:10]

        card = tk.Frame(self.frame_movimientos_stats, bg="white",
                        highlightthickness=1, highlightbackground="#e2e8f0")
        card.pack(fill="x")

        tk.Frame(card, bg="#3b82f6", height=4).pack(fill="x")

        if not prestamos:
            inner = tk.Frame(card, bg="white", padx=25, pady=30)
            inner.pack(fill="x")

            tk.Label(inner, text="No hay movimientos recientes",
                     font=("Segoe UI", 11),
                     bg="white", fg="#94a3b8").pack()
            return

        inner_card = tk.Frame(card, bg="white")
        inner_card.pack(fill="x")

        for i, p in enumerate(prestamos):
            if p.estado_prestamo == "activo":
                color_bg = "#dbeafe"
                color_fg = "#1e40af"
                estado_txt = "Activo"
            else:
                color_bg = "#d1fae5"
                color_fg = "#065f46"
                estado_txt = "Devuelto"

            fila = tk.Frame(inner_card, bg="white", padx=20, pady=12)
            fila.pack(fill="x")

            info = tk.Frame(fila, bg="white")
            info.pack(side="left", fill="x", expand=True)

            tk.Label(info,
                     text=f"Préstamo #{p.id_prestamo} - {p.nombre_usuario}",
                     font=("Segoe UI", 11, "bold"),
                     bg="white", fg="#0f172a",
                     anchor="w").pack(anchor="w")

            fecha = str(p.fecha_solicitud)[:10] if p.fecha_solicitud else "—"
            sub = tk.Frame(info, bg="white")
            sub.pack(anchor="w", pady=(3, 0))

            tk.Label(sub, text=fecha,
                     font=("Segoe UI", 9),
                     bg="white", fg="#64748b").pack(side="left")

            tk.Label(sub, text="  •  ",
                     font=("Segoe UI", 9),
                     bg="white", fg="#cbd5e1").pack(side="left")

            tk.Label(sub, text=f"  {estado_txt}  ",
                     font=("Segoe UI", 8, "bold"),
                     bg=color_bg, fg=color_fg,
                     padx=6, pady=1).pack(side="left")

            badge = tk.Frame(fila, bg="#f1f5f9",
                             highlightthickness=1, highlightbackground="#e2e8f0")
            badge.pack(side="right", padx=(10, 0))

            tk.Label(badge, text=f"{p.ejemplares_count}",
                     font=("Segoe UI", 12, "bold"),
                     bg="#f1f5f9", fg="#0f172a",
                     padx=12, pady=8).pack(side="left")

            if i < len(prestamos) - 1:
                tk.Frame(inner_card, bg="#f1f5f9",
                         height=1).pack(fill="x", padx=20)

    def _refrescar_comentarios_stats(self):
        for w in self.frame_comentarios.winfo_children():
            w.destroy()

        es_admin = self.auth.es_admin()
        u = self.auth.get_usuario_actual()

        if es_admin:
            comentarios = Comentario.obtener_todos()
        else:
            comentarios = Comentario.obtener_mis_comentarios(u.id_usuario) if u else []

        if not comentarios:
            tk.Label(self.frame_comentarios,
                     text="No hay comentarios registrados",
                     font=("Segoe UI", 11),
                     bg="white", fg="#94a3b8").pack(pady=30)
        else:
            for i, c in enumerate(comentarios):
                fila = tk.Frame(self.frame_comentarios, bg="white",
                                padx=20, pady=12)
                fila.pack(fill="x")

                info = tk.Frame(fila, bg="white")
                info.pack(side="left", fill="x", expand=True)

                estrellas = "⭐" * c["calificacion"]
                titulo_txt = c["titulo"] or "Sin título"
                if len(titulo_txt) > 45:
                    titulo_txt = titulo_txt[:45] + "..."

                tk.Label(info, text=f"{estrellas}  {titulo_txt}",
                         font=("Segoe UI", 11, "bold"),
                         bg="white", fg="#0f172a",
                         anchor="w").pack(anchor="w")

                if es_admin:
                    tk.Label(info, text=c['usuario'],
                             font=("Segoe UI", 9),
                             bg="white", fg="#64748b",
                             anchor="w").pack(anchor="w", pady=(2, 0))

                tk.Label(info, text=c["comentario"],
                         font=("Segoe UI", 10),
                         bg="white", fg="#475569",
                         wraplength=800, justify="left",
                         anchor="w").pack(anchor="w", pady=(5, 0))

                tk.Label(fila, text=c["fecha"][:10],
                         font=("Segoe UI", 9),
                         bg="white", fg="#94a3b8").pack(side="right", anchor="n")

                if i < len(comentarios) - 1:
                    tk.Frame(self.frame_comentarios, bg="#f1f5f9",
                             height=1).pack(fill="x", padx=20)

        if not es_admin:
            tk.Button(self.frame_comentarios, text="Escribir comentario",
                      font=("Segoe UI", 10, "bold"),
                      bg="#fef3c7", fg="#92400e",
                      activebackground="#fde68a",
                      bd=0, cursor="hand2", padx=20, pady=10,
                      command=self._abrir_selector_libro_comentar
                      ).pack(pady=15)

    def _abrir_selector_libro_comentar(self):
        u = self.auth.get_usuario_actual()
        if not u:
            return

        libros = Comentario.libros_para_comentar(u.id_usuario)

        if not libros:
            messagebox.showinfo("Sin libros",
                                "No tienes libros pendientes de comentar.\n\n"
                                "Pide un libro prestado y devuélvelo para poder comentarlo.")
            return

        w = tk.Toplevel(self)
        w.title("Seleccionar libro para comentar")
        w.geometry("520x400")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Selecciona un libro",
                 font=("Segoe UI", 15, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=25, pady=18)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=15)

        body = tk.Frame(w, bg="white", padx=20, pady=15)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        for libro in libros:
            fila = tk.Frame(body, bg="white", padx=10, pady=8,
                            highlightthickness=1, highlightbackground="#e2e8f0",
                            cursor="hand2")
            fila.pack(fill="x", pady=4)

            titulo_txt = libro["titulo"] or "Sin título"
            if len(titulo_txt) > 40:
                titulo_txt = titulo_txt[:40] + "..."

            tk.Label(fila, text=titulo_txt,
                     font=("Segoe UI", 11, "bold"),
                     bg="white", fg="#0f172a",
                     anchor="w").pack(anchor="w")

            tk.Label(fila, text=libro['autor'] or 'Autor desconocido',
                     font=("Segoe UI", 9),
                     bg="white", fg="#64748b",
                     anchor="w").pack(anchor="w", pady=(2, 0))

            def on_click(e, l=libro):
                w.destroy()
                self.escribir_comentario_home(l)

            for widget in [fila] + list(fila.winfo_children()):
                widget.bind("<Button-1>", on_click)

    def escribir_comentario_home(self, libro):
        u = self.auth.get_usuario_actual()
        if not u:
            return

        w = tk.Toplevel(self)
        w.title("Escribir Comentario")
        w.geometry("500x550")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)

        header = tk.Frame(w, bg="#0f172a", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Nuevo Comentario",
                 font=("Segoe UI", 15, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=25, pady=20)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=15)

        body = tk.Frame(w, bg="white", padx=25, pady=20)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(body, text=libro['titulo'],
                 font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#0f172a",
                 wraplength=400, justify="left").pack(anchor="w", pady=(0, 15))

        tk.Label(body, text="⭐ Calificación (1-5):",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 5))

        combo_cal = ttk.Combobox(body, values=[1, 2, 3, 4, 5],
                                  state="readonly", width=10,
                                  font=("Segoe UI", 11))
        combo_cal.set(5)
        combo_cal.pack(anchor="w", pady=(0, 15))

        tk.Label(body, text="Comentario:",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 5))

        txt = tk.Text(body, height=6, font=("Segoe UI", 10),
                      bg="#f8fafc", bd=1, relief="solid")
        txt.pack(fill="x", pady=(0, 15))

        def guardar():
            comentario = txt.get("1.0", "end").strip()
            if not comentario:
                messagebox.showwarning("Falta", "Escribe un comentario.", parent=w)
                return
            if len(comentario) < 5:
                messagebox.showwarning("Muy corto",
                                       "El comentario debe tener al menos 5 caracteres.",
                                       parent=w)
                return

            ok = Comentario.crear(u.id_usuario, libro["id_libro"],
                                  int(combo_cal.get()), comentario)
            if ok:
                messagebox.showinfo("Éxito",
                                    "✅ ¡Gracias por tu comentario!", parent=w)
                w.destroy()
                self._refresh_stats()
            else:
                messagebox.showerror("Error",
                                     "No se pudo guardar el comentario.", parent=w)

        tk.Button(body, text="Publicar Comentario",
                  font=("Segoe UI", 11, "bold"),
                  bg="#10b981", fg="white",
                  activebackground="#059669",
                  bd=0, cursor="hand2", padx=25, pady=10,
                  command=guardar).pack(pady=(5, 0))

    def _exportar_stats_pdf(self):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib.utils import ImageReader
            from auth_manager import obtener_ruta_logo

            es_admin = self.auth.es_admin()
            u_actual = self.auth.get_usuario_actual()

            total_libros = Libro.contar()
            total_ejemplares = Ejemplar.contar()
            disponibles = Ejemplar.contar_disponibles()
            prestados = total_ejemplares - disponibles

            if es_admin:
                total_usuarios = Usuario.contar()
                prestamos_activos = Prestamo.contar_activos()
                historial_total = Prestamo.contar_historial()
            else:
                prestamos_lista = Prestamo.obtener_activos()
                historial_lista = Prestamo.obtener_historial()
                if u_actual:
                    prestamos_lista = [p for p in prestamos_lista
                                       if p.nombre_usuario == u_actual.usuario_login]
                    historial_lista = [h for h in historial_lista
                                       if h.nombre_usuario == u_actual.usuario_login]
                prestamos_activos = len(prestamos_lista)
                historial_total = len(historial_lista)
                total_usuarios = None

            try:
                conn = get_connection()
                cursor = conn.cursor()
                if es_admin:
                    cursor.execute("""
                        SELECT TOP 5 l.Titulo, COUNT(pd.id_Detalle) AS Total
                        FROM Libros l
                        INNER JOIN PrestamoDetalle pd ON l.id_libro = pd.id_Libro
                        GROUP BY l.Titulo
                        ORDER BY Total DESC, l.Titulo
                    """)
                else:
                    cursor.execute("""
                        SELECT TOP 5 l.Titulo, COUNT(pd.id_Detalle) AS Total
                        FROM Libros l
                        INNER JOIN PrestamoDetalle pd ON l.id_libro = pd.id_Libro
                        INNER JOIN Prestamos p ON pd.id_Prestamo = p.id_Prestamo
                        WHERE p.id_Usuario = ?
                        GROUP BY l.Titulo
                        ORDER BY Total DESC, l.Titulo
                    """, (u_actual.id_usuario,))
                filas = cursor.fetchall()
                conn.close()
                top_libros = [(f[0], f[1]) for f in filas]
            except Exception:
                top_libros = []

            carpeta = os.path.join(os.path.expanduser("~"),
                                   "Documents", "EstadisticasBiblioteca")
            os.makedirs(carpeta, exist_ok=True)

            fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_pdf = os.path.join(carpeta, f"Estadisticas_{fecha_str}.pdf")

            c = pdf_canvas.Canvas(ruta_pdf, pagesize=letter)
            ancho, alto = letter

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
            c.setFont("Helvetica-Bold", 22)
            c.drawString(x_texto, alto - 50, "BIBLIOTECA UNI")

            c.setFillColorRGB(0.58, 0.64, 0.69)
            c.setFont("Helvetica", 10)
            c.drawString(x_texto, alto - 70, "Sistema de Gestión Bibliotecaria")

            titulo = "ESTADÍSTICAS GENERALES" if es_admin else "MIS ESTADÍSTICAS"
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(x_texto, alto - 95, titulo)

            c.setFillColorRGB(0.39, 0.45, 0.53)
            c.setFont("Helvetica", 9)
            c.drawRightString(ancho - 50, alto - 130,
                              f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

            if u_actual:
                c.drawRightString(ancho - 50, alto - 145,
                                  f"Usuario: {u_actual.usuario_login}")

            c.setStrokeColorRGB(0.88, 0.91, 0.94)
            c.line(50, alto - 165, ancho - 50, alto - 165)

            y = alto - 200
            c.setFillColorRGB(0.06, 0.09, 0.16)
            c.setFont("Helvetica-Bold", 13)
            c.drawString(50, y, "RESUMEN GENERAL")
            y -= 30

            datos = [
                ("Total de Libros", f"{total_libros:,}"),
                ("Total de Ejemplares", f"{total_ejemplares:,}"),
                ("Ejemplares Disponibles", f"{disponibles:,}"),
                ("Ejemplares Prestados", f"{prestados:,}"),
            ]
            if es_admin:
                datos.append(("Total de Usuarios", f"{total_usuarios:,}"))
            datos.append(("Préstamos Activos", f"{prestamos_activos:,}"))
            datos.append(("Préstamos Históricos", f"{historial_total:,}"))

            for etiqueta, valor in datos:
                c.setFillColorRGB(0.97, 0.98, 0.99)
                c.rect(50, y - 20, ancho - 100, 22, fill=True, stroke=False)

                c.setFillColorRGB(0.39, 0.45, 0.53)
                c.setFont("Helvetica", 10)
                c.drawString(65, y - 13, etiqueta)

                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.setFont("Helvetica-Bold", 11)
                c.drawRightString(ancho - 65, y - 13, valor)

                y -= 28

            if top_libros:
                y -= 20
                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.setFont("Helvetica-Bold", 13)
                c.drawString(50, y, "TOP 5 LIBROS MÁS PRESTADOS")
                y -= 30

                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.rect(50, y - 20, ancho - 100, 22, fill=True, stroke=False)

                c.setFillColorRGB(1, 1, 1)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(65, y - 13, "Título")
                c.drawRightString(ancho - 65, y - 13, "Préstamos")
                y -= 28

                for i, (titulo_libro, total) in enumerate(top_libros):
                    if i % 2 == 0:
                        c.setFillColorRGB(0.97, 0.98, 0.99)
                        c.rect(50, y - 20, ancho - 100, 22, fill=True, stroke=False)

                    c.setFillColorRGB(0.06, 0.09, 0.16)
                    c.setFont("Helvetica", 10)
                    texto = (titulo_libro[:60] + "…"
                             if len(titulo_libro) > 60 else titulo_libro)
                    c.drawString(65, y - 13, texto)

                    c.setFillColorRGB(0.22, 0.74, 0.97)
                    c.setFont("Helvetica-Bold", 11)
                    c.drawRightString(ancho - 65, y - 13, str(total))

                    y -= 28

            c.setFillColorRGB(0.58, 0.64, 0.69)
            c.setFont("Helvetica", 8)
            c.drawCentredString(ancho / 2, 50,
                                "Documento generado automáticamente por el Sistema de Biblioteca UNI")

            c.save()

            try:
                os.startfile(ruta_pdf)
                messagebox.showinfo("PDF generado",
                                    f"✅ Estadísticas exportadas:\n\n{ruta_pdf}")
            except Exception:
                messagebox.showinfo("PDF generado",
                                    f"✅ Archivo guardado en:\n\n{ruta_pdf}")

        except ImportError:
            messagebox.showerror("Error",
                                 "Falta instalar 'reportlab':\n\npip install reportlab")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n\n{e}")

    def _dibujar_graficos(self, disponibles, prestados):
        for w in self.frame_pastel.winfo_children():
            w.destroy()
        for w in self.frame_barras.winfo_children():
            w.destroy()

        total = disponibles + prestados
        es_admin = self.auth.es_admin()

        fig1 = Figure(figsize=(4.5, 1.9), dpi=70, facecolor="white")
        ax1 = fig1.add_subplot(111)

        if total > 0:
            valores = [disponibles, prestados]
            colores = ["#10b981", "#f59e0b"]

            ax1.pie(valores, colors=colores, startangle=90,
                    wedgeprops=dict(width=0.35, edgecolor="white", linewidth=3))

            try:
                circle = Circle((0, 0), 0.56, fc="white", ec="none")
                ax1.add_patch(circle)
            except Exception:
                pass

            ax1.text(0, 0.12, f"{total}", ha="center", va="center",
                     fontsize=18, fontweight="bold", color="#0f172a")
            ax1.text(0, -0.22, "ejemplares", ha="center", va="center",
                     fontsize=7, color="#94a3b8")

            leyenda = f"{disponibles} disponibles   |   {prestados} prestados"
            ax1.text(0, -1.35, leyenda, ha="center", va="center",
                     fontsize=8, color="#475569")
        else:
            ax1.text(0, 0, "Sin ejemplares", ha="center", va="center",
                     fontsize=10, color="#94a3b8")
            ax1.axis("off")

        ax1.set_title("Disponibilidad de Ejemplares",
                      fontsize=10, fontweight="bold",
                      color="#0f172a", pad=6)

        fig1.tight_layout(pad=0.3)
        canvas1 = FigureCanvasTkAgg(fig1, master=self.frame_pastel)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

        try:
            conn = get_connection()
            cursor = conn.cursor()
            u_actual = self.auth.get_usuario_actual()

            if es_admin:
                cursor.execute("""
                    SELECT TOP 5 l.Titulo, COUNT(pd.id_Detalle) AS Total
                    FROM Libros l
                    INNER JOIN PrestamoDetalle pd ON l.id_libro = pd.id_Libro
                    GROUP BY l.Titulo
                    ORDER BY Total DESC, l.Titulo
                """)
            else:
                cursor.execute("""
                    SELECT TOP 5 l.Titulo, COUNT(pd.id_Detalle) AS Total
                    FROM Libros l
                    INNER JOIN PrestamoDetalle pd ON l.id_libro = pd.id_Libro
                    INNER JOIN Prestamos p ON pd.id_Prestamo = p.id_Prestamo
                    WHERE p.id_Usuario = ?
                    GROUP BY l.Titulo
                    ORDER BY Total DESC, l.Titulo
                """, (u_actual.id_usuario,))

            filas = cursor.fetchall()
            conn.close()
            titulos = [(f[0][:18] + "…" if len(f[0]) > 18 else f[0]) for f in filas]
            totales = [f[1] for f in filas]
        except Exception:
            titulos = ["Sin datos"]
            totales = [0]

        fig2 = Figure(figsize=(4.5, 1.9), dpi=70, facecolor="white")
        ax2 = fig2.add_subplot(111)

        if any(t > 0 for t in totales):
            colores_bar = ["#3b82f6", "#60a5fa", "#38bdf8",
                           "#22d3ee", "#06b6d4"][:len(titulos)]
            bars = ax2.barh(titulos, totales, color=colores_bar,
                            edgecolor="none", height=0.6)

            for bar in bars:
                w = bar.get_width()
                ax2.text(w + max(totales) * 0.03,
                         bar.get_y() + bar.get_height() / 2,
                         f"{int(w)}", va="center", fontsize=8,
                         color="#0f172a", fontweight="bold")

            ax2.set_xlim(0, max(totales) * 1.2 if max(totales) > 0 else 1)
            ax2.invert_yaxis()
        else:
            ax2.text(0.5, 0.5, "Sin préstamos registrados aún",
                     ha="center", va="center", fontsize=10, color="#94a3b8",
                     transform=ax2.transAxes)

        titulo_grafico = ("Top 5 Libros Más Prestados" if es_admin
                          else "Mis Libros Más Prestados")
        ax2.set_title(titulo_grafico, fontsize=10, fontweight="bold",
                      color="#0f172a", pad=6)
        ax2.tick_params(axis="both", labelsize=7, colors="#64748b", length=0)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.spines["bottom"].set_visible(False)
        ax2.spines["left"].set_visible(False)
        ax2.set_xticks([])
        ax2.grid(False)

        fig2.tight_layout(pad=0.3)
        canvas2 = FigureCanvasTkAgg(fig2, master=self.frame_barras)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)

    def _crear_boton_menu(self, key, icono, texto):
        btn_frame = tk.Frame(self.sidebar, bg="#0f172a", cursor="hand2")
        btn_frame.pack(fill="x", padx=15, pady=2)

        contenido = tk.Frame(btn_frame, bg="#0f172a")
        contenido.pack(fill="x", padx=12, pady=11)

        lbl_texto = tk.Label(contenido, text=texto, font=("Segoe UI", 11),
                             bg="#0f172a", fg="#cbd5e1", anchor="w")
        lbl_texto.pack(side="left")

        indicador = tk.Frame(btn_frame, bg="#0f172a", width=4)

        btn_frame.texto = lbl_texto
        btn_frame.indicador = indicador
        btn_frame.contenido = contenido
        btn_frame.key = key

        def on_enter(e):
            if self.vista_actual != key:
                for w in [btn_frame, contenido, lbl_texto]:
                    w.config(bg="#1e293b")

        def on_leave(e):
            if self.vista_actual != key:
                for w in [btn_frame, contenido, lbl_texto]:
                    w.config(bg="#0f172a")

        def on_click(e):
            self.mostrar_vista(key)

        for w in [btn_frame, contenido, lbl_texto]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

        return btn_frame

    def mostrar_vista(self, key):
        for k, btn in self.botones_menu.items():
            btn.config(bg="#0f172a")
            btn.texto.config(bg="#0f172a", fg="#cbd5e1")
            btn.contenido.config(bg="#0f172a")
            btn.indicador.pack_forget()

        btn = self.botones_menu[key]
        btn.config(bg="#1e293b")
        btn.texto.config(bg="#1e293b", fg="#f1f5f9")
        btn.contenido.config(bg="#1e293b")
        btn.indicador.config(bg="#38bdf8")
        btn.indicador.pack(side="left", fill="y", before=btn.contenido)

        titulos = {
            "home": "Inicio",
            "libros": "Catálogo de Libros",
            "ejemplares": "Gestión de Ejemplares",
            "prestamos": "Gestión de Préstamos",
            "usuarios": "Gestión de Usuarios",
            "stats": "Estadísticas",
        }
        self.lbl_titulo_seccion.config(text=titulos.get(key, ""))

        for v in self.vistas.values():
            v.grid_remove()

        self.vistas[key].grid()
        if hasattr(self.vistas[key], 'on_show'):
            self.vistas[key].on_show()

        if key == "home":
            self._refrescar_home()
        elif key == "stats":
            self._refresh_stats()

        self.vista_actual = key

    def _actualizar_reloj(self):
        ahora = datetime.now()
        dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

        hora_12 = ahora.strftime("%I:%M %p").lstrip("0")
        texto = (f"{dias[ahora.weekday()]} {ahora.day} "
                 f"{meses[ahora.month - 1]} · {hora_12}")

        self.lbl_reloj.config(text=texto)
        self.after(30000, self._actualizar_reloj)

    def _verificar_notificaciones(self):
        try:
            prestamos = Prestamo.obtener_activos()
            vencidos = 0
            hoy = datetime.now().date()

            for p in prestamos:
                if p.fecha_devolucion_esperada:
                    try:
                        fecha_dev = datetime.strptime(
                            str(p.fecha_devolucion_esperada)[:10],
                            "%Y-%m-%d").date()
                        if fecha_dev < hoy:
                            vencidos += 1
                    except Exception:
                        pass

            if vencidos > 0:
                self.lbl_badge.config(text=str(vencidos))
                self.lbl_badge.place(in_=self.btn_notif, relx=0.7, rely=0.05)
            else:
                self.lbl_badge.place_forget()
        except Exception:
            pass

        self.after(60000, self._verificar_notificaciones)

    def _mostrar_notificaciones(self):
        vencidos, proximos = [], []
        hoy = datetime.now().date()

        try:
            for p in Prestamo.obtener_activos():
                if p.fecha_devolucion_esperada:
                    try:
                        fecha_dev = datetime.strptime(
                            str(p.fecha_devolucion_esperada)[:10],
                            "%Y-%m-%d").date()
                        dias = (fecha_dev - hoy).days
                        if dias < 0:
                            vencidos.append((p, abs(dias)))
                        elif dias <= 3:
                            proximos.append((p, dias))
                    except Exception:
                        pass
        except Exception:
            pass

        w = tk.Toplevel(self)
        w.title("Notificaciones")
        w.geometry("500x540")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="Notificaciones",
                 font=("Segoe UI", 17, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=25, pady=20)

        tk.Button(header, text="Cerrar",
                  font=("Segoe UI", 11, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=w.destroy).pack(side="right", padx=25, pady=20)

        body = tk.Frame(w, bg="#f1f5f9", padx=20, pady=20)
        body.pack(fill="both", expand=True)

        if not vencidos and not proximos:
            tk.Label(body, text="No hay notificaciones pendientes",
                     font=("Segoe UI", 13), bg="#f1f5f9",
                     fg="#16a34a").pack(pady=50)
            return

        if vencidos:
            tk.Label(body, text=f"Préstamos VENCIDOS ({len(vencidos)})",
                     font=("Segoe UI", 11, "bold"), bg="#f1f5f9",
                     fg="#dc2626", anchor="w").pack(fill="x", pady=(0, 8))

            for p, dias in vencidos:
                card = tk.Frame(body, bg="#fee2e2", padx=15, pady=10)
                card.pack(fill="x", pady=3)
                tk.Label(card, text=f"Préstamo #{p.id_prestamo}",
                         font=("Segoe UI", 10, "bold"),
                         bg="#fee2e2", fg="#991b1b").pack(anchor="w")
                tk.Label(card,
                         text=f"Usuario: {p.nombre_usuario} - Vencido hace {dias} días",
                         font=("Segoe UI", 9), bg="#fee2e2",
                         fg="#7f1d1d").pack(anchor="w")

        if proximos:
            tk.Label(body, text=f"Próximos a vencer ({len(proximos)})",
                     font=("Segoe UI", 11, "bold"), bg="#f1f5f9",
                     fg="#ea580c", anchor="w").pack(fill="x", pady=(15, 8))

            for p, dias in proximos:
                card = tk.Frame(body, bg="#fed7aa", padx=15, pady=10)
                card.pack(fill="x", pady=3)
                tk.Label(card, text=f"Préstamo #{p.id_prestamo}",
                         font=("Segoe UI", 10, "bold"),
                         bg="#fed7aa", fg="#9a3412").pack(anchor="w")
                if dias == 0:
                    txt = f"Usuario: {p.nombre_usuario} - Vence hoy"
                else:
                    txt = f"Usuario: {p.nombre_usuario} - Vence en {dias} días"
                tk.Label(card, text=txt, font=("Segoe UI", 9),
                         bg="#fed7aa", fg="#7c2d12").pack(anchor="w")

    def on_show(self):
        pass

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión",
                               "¿Deseas cerrar sesión?\n\n"
                               "Volverás a la pantalla de inicio de sesión."):
            try:
                root = self.winfo_toplevel()
                if hasattr(root, 'mostrar_login'):
                    root.mostrar_login()
                else:
                    self.auth.reiniciar_sesion()
            except Exception:
                pass

    def _cerrar_sistema(self):
        if messagebox.askyesno("Cerrar Sistema",
                               "¿Estás seguro que deseas cerrar la aplicación?\n\n"
                               "Se cerrará la sesión y saldrás del sistema."):
            try:
                self.winfo_toplevel().destroy()
            except Exception:
                pass