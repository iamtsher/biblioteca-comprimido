import os
import tkinter as tk
from tkinter import messagebox

from auth_manager import AuthManager, quitar_boton_cerrar

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except ImportError:
    PIL_OK = False


class LoginView(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg="#ffffff")
        self.auth = AuthManager()
        self.logo_img = None
        self.mostrar_pass = False
        self._build_ui()

    def _crear_logo_libro(self, tamaño=400):
        img = Image.new("RGBA", (tamaño, tamaño), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        azul_oscuro = (30, 58, 138, 255)
        azul_medio = (59, 130, 246, 255)
        blanco = (255, 255, 255, 255)
        amarillo = (250, 204, 21, 255)
        crema = (254, 249, 195, 255)

        cx, cy = tamaño // 2, tamaño // 2

        sombra = Image.new("RGBA", (tamaño, tamaño), (0, 0, 0, 0))
        sombra_draw = ImageDraw.Draw(sombra)
        sombra_draw.ellipse(
            (cx - 170, cy - 160, cx + 170, cy + 180),
            fill=(0, 0, 0, 40)
        )
        img = Image.alpha_composite(img, sombra)
        draw = ImageDraw.Draw(img)

        pagina_izq = [
            (cx - 130, cy - 90),
            (cx - 5, cy - 110),
            (cx - 5, cy + 120),
            (cx - 130, cy + 100),
        ]
        draw.polygon(pagina_izq, fill=crema, outline=azul_oscuro)

        pagina_der = [
            (cx + 5, cy - 110),
            (cx + 130, cy - 90),
            (cx + 130, cy + 100),
            (cx + 5, cy + 120),
        ]
        draw.polygon(pagina_der, fill=blanco, outline=azul_oscuro)

        draw.line(
            [(cx, cy - 110), (cx, cy + 120)],
            fill=azul_oscuro, width=6
        )

        for i in range(6):
            y = cy - 70 + i * 28
            ancho = 100 if i % 2 == 0 else 80
            draw.line(
                [(cx - 115, y), (cx - 115 + ancho, y)],
                fill=azul_medio, width=4
            )

        for i in range(6):
            y = cy - 70 + i * 28
            ancho = 100 if i % 2 == 1 else 80
            draw.line(
                [(cx + 15, y), (cx + 15 + ancho, y)],
                fill=azul_medio, width=4
            )

        draw.line(
            [(cx - 140, cy + 100), (cx - 5, cy + 120)],
            fill=azul_oscuro, width=14
        )
        draw.line(
            [(cx + 5, cy + 120), (cx + 140, cy + 100)],
            fill=azul_oscuro, width=14
        )

        marcador = [
            (cx + 80, cy - 110),
            (cx + 100, cy - 110),
            (cx + 100, cy - 40),
            (cx + 90, cy - 55),
            (cx + 80, cy - 40),
        ]
        draw.polygon(marcador, fill=amarillo)

        brillo = Image.new("RGBA", (tamaño, tamaño), (0, 0, 0, 0))
        brillo_draw = ImageDraw.Draw(brillo)
        brillo_draw.ellipse(
            (cx - 140, cy - 130, cx + 60, cy - 60),
            fill=(255, 255, 255, 60)
        )
        img = Image.alpha_composite(img, brillo)

        return img

    def _cargar_logo(self, size=200):
        if not PIL_OK:
            return None
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            rutas = [
                os.path.join(base_dir, "logo_libro.png"),
                os.path.join(base_dir, "logo_libro.jpeg"),
                os.path.join(base_dir, "logo_libro.jpg"),
                os.path.join(base_dir, "logo_unai.png"),
                os.path.join(base_dir, "logo_unai.jpeg"),
                os.path.join(base_dir, "logo_unai.jpg"),
            ]
            ruta_logo = next((r for r in rutas if os.path.exists(r)), None)

            if ruta_logo:
                img = Image.open(ruta_logo).convert("RGBA")
            else:
                img = self._crear_logo_libro(400)

            img.thumbnail((size, size), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _build_ui(self):
        left = tk.Frame(self, bg="#1e3a8a")
        left.place(x=0, y=0, relwidth=0.65, relheight=1)
        left.pack_propagate(False)

        centrado = tk.Frame(left, bg="#1e3a8a")
        centrado.place(relx=0.5, rely=0.5, anchor="center")

        self.logo_img = self._cargar_logo(size=220)
        if self.logo_img:
            tk.Label(centrado, image=self.logo_img,
                     bg="#1e3a8a").pack(pady=(0, 25))
        else:
            tk.Label(centrado, text="📚",
                     font=("Segoe UI Emoji", 85),
                     bg="#1e3a8a", fg="#ffffff").pack(pady=(0, 25))

        tk.Label(centrado, text="BIBLIOTECA",
                 font=("Segoe UI", 30, "bold"),
                 bg="#1e3a8a", fg="#93c5fd").pack()

        tk.Label(centrado, text="UNI",
                 font=("Segoe UI", 44, "bold"),
                 bg="#1e3a8a", fg="#ffffff").pack(pady=(0, 10))

        tk.Frame(centrado, bg="#3b82f6", height=3, width=340).pack(pady=(0, 15))

        tk.Label(centrado, text="Sistema de Gestión Bibliotecaria",
                 font=("Segoe UI", 13, "bold"),
                 bg="#1e3a8a", fg="#dbeafe").pack()

        tk.Label(centrado, text="Universidad Nacional de Ingeniería",
                 font=("Segoe UI", 11),
                 bg="#1e3a8a", fg="#93c5fd").pack(pady=(5, 0))

        footer = tk.Frame(left, bg="#1e3a8a")
        footer.pack(side="bottom", fill="x", pady=15)

        tk.Label(footer, text="© 2026 · Todos los derechos reservados",
                 font=("Segoe UI", 9, "bold"),
                 bg="#1e3a8a", fg="#93c5fd").pack()

        tk.Label(footer, text="Universidad Nacional de Ingeniería",
                 font=("Segoe UI", 8),
                 bg="#1e3a8a", fg="#60a5fa").pack(pady=(2, 0))

        right = tk.Frame(self, bg="#ffffff")
        right.place(relx=0.65, y=0, relwidth=0.35, relheight=1)

        tk.Button(
            right, text="✖  Salir",
            font=("Segoe UI", 10, "bold"),
            bg="#ffffff", fg="#ef4444",
            activebackground="#fee2e2", activeforeground="#dc2626",
            bd=0, cursor="hand2", padx=20, pady=10,
            command=self._confirmar_salir
        ).place(relx=1.0, rely=0.0, x=-25, y=25, anchor="ne")

        self._construir_formulario(right)

    def _construir_formulario(self, right):
        form_container = tk.Frame(right, bg="#ffffff")
        form_container.place(relx=0.5, rely=0.5, anchor="center")

        form = tk.Frame(form_container, bg="#ffffff")
        form.pack(padx=30)

        tk.Label(form, text="Iniciar Sesión",
                 font=("Segoe UI", 28, "bold"),
                 bg="#ffffff", fg="#0f172a").pack(anchor="w")

        tk.Label(form, text="Ingresa tus credenciales",
                 font=("Segoe UI", 11),
                 bg="#ffffff", fg="#64748b").pack(anchor="w", pady=(6, 35))

        tk.Label(form, text="Usuario",
                 font=("Segoe UI", 11, "bold"),
                 bg="#ffffff", fg="#334155").pack(anchor="w", pady=(0, 8))

        user_frame = tk.Frame(form, bg="#f8fafc",
                              highlightthickness=1,
                              highlightbackground="#e2e8f0",
                              highlightcolor="#1e3a8a")
        user_frame.pack(fill="x", pady=(0, 20))

        tk.Label(user_frame, text="👤", font=("Segoe UI Emoji", 13),
                 bg="#f8fafc", fg="#64748b").pack(side="left", padx=(12, 8))

        self.entry_user = tk.Entry(user_frame, font=("Segoe UI", 12),
                                   bg="#f8fafc", fg="#0f172a",
                                   insertbackground="#1e3a8a",
                                   bd=0, highlightthickness=0)
        self.entry_user.pack(side="left", fill="x", expand=True,
                             padx=(0, 12), pady=14)

        tk.Label(form, text="Contraseña",
                 font=("Segoe UI", 11, "bold"),
                 bg="#ffffff", fg="#334155").pack(anchor="w", pady=(0, 8))

        pass_frame = tk.Frame(form, bg="#f8fafc",
                              highlightthickness=1,
                              highlightbackground="#e2e8f0",
                              highlightcolor="#1e3a8a")
        pass_frame.pack(fill="x", pady=(0, 12))

        tk.Label(pass_frame, text="🔒", font=("Segoe UI Emoji", 13),
                 bg="#f8fafc", fg="#64748b").pack(side="left", padx=(12, 8))

        self.entry_pass = tk.Entry(pass_frame, font=("Segoe UI", 12),
                                   bg="#f8fafc", fg="#0f172a",
                                   insertbackground="#1e3a8a",
                                   bd=0, highlightthickness=0, show="•")
        self.entry_pass.pack(side="left", fill="x", expand=True,
                             padx=(0, 5), pady=14)

        self.btn_ojo = tk.Button(
            pass_frame, text="👁️",
            font=("Segoe UI Emoji", 12),
            bg="#f8fafc", fg="#94a3b8",
            bd=0, cursor="hand2",
            activebackground="#f8fafc",
            activeforeground="#1e3a8a",
            relief="flat",
            command=self._toggle_password
        )
        self.btn_ojo.pack(side="right", padx=(0, 10))

        olvido_frame = tk.Frame(form, bg="#ffffff")
        olvido_frame.pack(fill="x", pady=(0, 22))

        lbl_olvido = tk.Label(olvido_frame, text="¿Olvidaste tu contraseña?",
                              font=("Segoe UI", 9, "underline"),
                              bg="#ffffff", fg="#1e3a8a",
                              cursor="hand2")
        lbl_olvido.pack(side="right")
        lbl_olvido.bind("<Button-1>", lambda e: self._recuperar_contrasena())

        self.btn_login = tk.Button(
            form, text="INICIAR SESIÓN  →",
            font=("Segoe UI", 13, "bold"),
            bg="#1e3a8a", fg="#ffffff",
            activebackground="#1e40af", activeforeground="#ffffff",
            bd=0, cursor="hand2", pady=16,
            command=self._do_login
        )
        self.btn_login.pack(fill="x", pady=(0, 22))

        self.btn_login.bind("<Enter>", lambda e: self.btn_login.config(bg="#1e40af"))
        self.btn_login.bind("<Leave>", lambda e: self.btn_login.config(bg="#1e3a8a"))

        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda e: self._do_login())

        self.after(100, lambda: self.entry_user.focus())

    def _toggle_password(self):
        if self.mostrar_pass:
            self.entry_pass.config(show="•")
            self.btn_ojo.config(text="👁️", fg="#94a3b8")
            self.mostrar_pass = False
        else:
            self.entry_pass.config(show="")
            self.btn_ojo.config(text="🙈", fg="#1e3a8a")
            self.mostrar_pass = True

    def _do_login(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()

        if not user or not pwd:
            messagebox.showwarning("Campos vacíos",
                                   "Ingresa usuario y contraseña.")
            return

        try:
            exito, msg = self.auth.login(user, pwd)
        except Exception as e:
            messagebox.showerror("Error de conexión",
                                 f"No se pudo conectar a la BD:\n\n{e}")
            return

        if exito:
            self._limpiar_formulario()
            self.auth.mostrar_vista("dashboard")
        else:
            messagebox.showerror("Error", msg)
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.focus()

    def _limpiar_formulario(self):
        self.entry_user.delete(0, tk.END)
        self.entry_pass.delete(0, tk.END)
        self.mostrar_pass = False
        self.entry_pass.config(show="•")
        self.btn_ojo.config(text="👁️", fg="#94a3b8")

    def _confirmar_salir(self):
        if messagebox.askyesno("Salir del Sistema",
                               "¿Estás seguro que deseas salir?\n\n"
                               "Se cerrará la aplicación por completo."):
            try:
                self.winfo_toplevel().destroy()
            except Exception as e:
                print(f"Error al salir: {e}")

    def _recuperar_contrasena(self):
        from models import Usuario

        w = tk.Toplevel(self)
        w.title("Recuperar Contraseña")
        w.geometry("480x560")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)

        w.after(10, lambda: quitar_boton_cerrar(w))

        header = tk.Frame(w, bg="#1e3a8a", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔐  Recuperar Contraseña",
                 font=("Segoe UI", 16, "bold"),
                 bg="#1e3a8a", fg="#ffffff").pack(side="left", padx=25, pady=22)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=15, pady=6,
                  command=w.destroy).pack(side="right", padx=20, pady=20)

        body = tk.Frame(w, bg="white", padx=35, pady=25)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(body, text="Recupera tu acceso",
                 font=("Segoe UI", 18, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        tk.Label(body, text="Ingresa tu usuario y una nueva contraseña",
                 font=("Segoe UI", 10),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(5, 20))

        entry_usuario = self._campo(body, "👤  Usuario")
        entry_nueva = self._campo(body, "🔒  Nueva contraseña", show="•")
        entry_confirm = self._campo(body, "🔒  Confirmar contraseña", show="•")

        def guardar():
            usuario = entry_usuario.get().strip()
            nueva = entry_nueva.get().strip()
            confirm = entry_confirm.get().strip()

            if not usuario:
                messagebox.showwarning("Campo requerido",
                                       "Ingresa tu usuario.", parent=w)
                entry_usuario.focus()
                return
            if not nueva:
                messagebox.showwarning("Campo requerido",
                                       "Ingresa la nueva contraseña.", parent=w)
                entry_nueva.focus()
                return
            if not confirm:
                messagebox.showwarning("Campo requerido",
                                       "Confirma la nueva contraseña.", parent=w)
                entry_confirm.focus()
                return
            if nueva != confirm:
                messagebox.showwarning("No coinciden",
                                       "Las contraseñas no coinciden.", parent=w)
                entry_confirm.delete(0, tk.END)
                entry_confirm.focus()
                return
            if len(nueva) < 4:
                messagebox.showwarning("Muy corta",
                                       "La contraseña debe tener al menos 4 caracteres.",
                                       parent=w)
                entry_nueva.focus()
                return

            u = Usuario.obtener_por_login(usuario)

            if not u:
                messagebox.showerror("Usuario no encontrado",
                                     f"El usuario '{usuario}' no existe o está inactivo.",
                                     parent=w)
                entry_usuario.delete(0, tk.END)
                entry_usuario.focus()
                return

            try:
                u.contrasena = nueva
                u.guardar()

                messagebox.showinfo("Éxito",
                                    f"✅ Contraseña actualizada para '{usuario}'.\n\n"
                                    f"Ya puedes iniciar sesión.",
                                    parent=w)
                w.destroy()

                self.entry_user.delete(0, tk.END)
                self.entry_user.insert(0, usuario)
                self.entry_pass.focus()
            except Exception as e:
                messagebox.showerror("Error",
                                     f"No se pudo actualizar:\n\n{e}",
                                     parent=w)

        tk.Button(body, text="🔐  Cambiar Contraseña",
                  font=("Segoe UI", 11, "bold"),
                  bg="#1e3a8a", fg="white",
                  activebackground="#1e40af", activeforeground="white",
                  bd=0, cursor="hand2", padx=30, pady=12,
                  command=guardar).pack(pady=(15, 0))

        entry_usuario.focus()

    def _campo(self, parent, label, show=None):
        tk.Label(parent, text=label,
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 5))

        entry = tk.Entry(parent, font=("Segoe UI", 11),
                         bg="#f8fafc", bd=1, relief="solid",
                         show=show if show else "")
        entry.pack(fill="x", ipady=7, pady=(0, 15))
        return entry