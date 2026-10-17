import os
import tkinter as tk
from tkinter import ttk, messagebox

from models import Usuario
from auth_manager import AuthManager, quitar_boton_cerrar

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


class UsuariosView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f1f5f9")
        self.auth = AuthManager()
        self.mostrando_papelera = False
        self._build_ui()

    def on_show(self):
        self.cargar_usuarios()

    def _build_ui(self):
        header = tk.Frame(self, bg="#f1f5f9", height=55)
        header.pack(fill="x", padx=25, pady=(12, 0))
        header.pack_propagate(False)

        self.lbl_contador = tk.Label(header, text="",
                                     font=("Segoe UI", 12, "bold"),
                                     bg="#f1f5f9", fg="#475569")
        self.lbl_contador.pack(side="left", pady=20)

        tk.Button(header, text="＋  Nuevo Usuario",
                  font=("Segoe UI", 11, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=self.abrir_form).pack(side="right", pady=8)

        self.btn_papelera = tk.Button(
            header, text="🗑️  Papelera",
            font=("Segoe UI", 11, "bold"),
            bg="#64748b", fg="white",
            activebackground="#475569", activeforeground="white",
            bd=0, cursor="hand2", padx=20, pady=8,
            command=self.toggle_papelera)
        self.btn_papelera.pack(side="right", padx=(0, 10), pady=8)

        buscar_frame = tk.Frame(self, bg="white", highlightthickness=1,
                                highlightbackground="#e2e8f0")
        buscar_frame.pack(fill="x", padx=25, pady=(15, 15))

        tk.Label(buscar_frame, text="🔍",
                 font=("Segoe UI", 14),
                 bg="white", fg="#64748b").pack(side="left", padx=(20, 8))

        self.entry_buscar = ttk.Entry(buscar_frame, width=45, font=("Segoe UI", 10))
        self.entry_buscar.pack(side="left", padx=5, pady=15)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar())

        tk.Button(buscar_frame, text="Buscar",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1e293b", fg="white",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.buscar).pack(side="left", padx=5)

        tk.Button(buscar_frame, text="Mostrar Todos",
                  font=("Segoe UI", 10),
                  bg="#e2e8f0", fg="#1e293b",
                  bd=0, cursor="hand2", padx=18, pady=8,
                  command=self.cargar_usuarios).pack(side="left", padx=5)

        container_outer = tk.Frame(self, bg="#f1f5f9")
        container_outer.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(container_outer, bg="#f1f5f9", highlightthickness=0)
        scroll = tk.Scrollbar(container_outer, orient="vertical",
                              command=self.canvas.yview)
        self.frame_usuarios = tk.Frame(self.canvas, bg="#f1f5f9")

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.frame_usuarios, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.frame_usuarios.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.frame_usuarios.grid_columnconfigure(0, weight=1, uniform="col")
        self.frame_usuarios.grid_columnconfigure(1, weight=1, uniform="col")
        self.frame_usuarios.grid_columnconfigure(2, weight=1, uniform="col")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _limpiar_tarjetas(self):
        for w in self.frame_usuarios.winfo_children():
            w.destroy()

    def toggle_papelera(self):
        self.mostrando_papelera = not self.mostrando_papelera
        if self.mostrando_papelera:
            self.btn_papelera.config(text="⬅️  Volver", bg="#f59e0b",
                                     activebackground="#d97706")
        else:
            self.btn_papelera.config(text="🗑️  Papelera", bg="#64748b",
                                     activebackground="#475569")
        self.cargar_usuarios()

    def _campo_password(self, parent, label, show_eye=True):
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill="x", pady=(0, 6))

        tk.Label(frame, text=label,
                 font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 2))

        entry_frame = tk.Frame(frame, bg="#f8fafc",
                               highlightthickness=1,
                               highlightbackground="#e2e8f0")
        entry_frame.pack(fill="x")

        entry = tk.Entry(entry_frame, font=("Segoe UI", 10),
                         bg="#f8fafc", fg="#0f172a",
                         bd=0, highlightthickness=0,
                         show="•")
        entry.pack(side="left", fill="x", expand=True,
                   padx=(8, 4), pady=4)

        if show_eye:
            def toggle():
                if entry.cget("show") == "•":
                    entry.config(show="")
                    btn.config(text="🙈", fg="#1e3a8a")
                else:
                    entry.config(show="•")
                    btn.config(text="👁️", fg="#94a3b8")

            btn = tk.Button(entry_frame, text="👁️",
                            font=("Segoe UI Emoji", 9),
                            bg="#f8fafc", fg="#94a3b8",
                            bd=0, cursor="hand2",
                            activebackground="#f8fafc",
                            activeforeground="#1e3a8a",
                            relief="flat",
                            command=toggle)
            btn.pack(side="right", padx=(0, 6))

        return entry

    def _crear_tarjeta(self, parent, usuario, fila, columna):
        es_admin = usuario.rol == "Admin"
        yo = self.auth.get_usuario_actual()
        es_yo_mismo = (yo and usuario.id_usuario == yo.id_usuario)

        if es_admin:
            color_rol, bg_rol, fg_rol, icono_rol = (
                "#ef4444", "#fee2e2", "#991b1b", "👑")
        else:
            color_rol, bg_rol, fg_rol, icono_rol = (
                "#3b82f6", "#dbeafe", "#1e40af", "👤")

        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")

        tk.Frame(card, bg=color_rol, height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=15, pady=12)

        top = tk.Frame(inner, bg="white")
        top.pack(fill="x")

        foto_frame = tk.Frame(top, bg=color_rol, width=48, height=48)
        foto_frame.pack(side="left")
        foto_frame.pack_propagate(False)

        foto_cargada = False
        if PIL_OK and getattr(usuario, "foto_perfil", None) and \
                os.path.exists(usuario.foto_perfil):
            try:
                img = Image.open(usuario.foto_perfil).convert("RGBA")
                img = img.resize((48, 48), Image.LANCZOS)
                foto_img = ImageTk.PhotoImage(img)

                lbl_foto = tk.Label(foto_frame, image=foto_img, bg=color_rol)
                lbl_foto.image = foto_img
                lbl_foto.pack(expand=True)
                foto_cargada = True
            except Exception:
                pass

        if not foto_cargada:
            inicial = usuario.usuario_login[0].upper() if usuario.usuario_login else "?"
            tk.Label(foto_frame, text=inicial,
                     font=("Segoe UI", 18, "bold"),
                     bg=color_rol, fg="white").pack(expand=True)

        info_top = tk.Frame(top, bg="white")
        info_top.pack(side="left", padx=(12, 0), fill="x", expand=True)

        tk.Label(info_top, text=usuario.usuario_login,
                 font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#0f172a",
                 anchor="w").pack(anchor="w")

        tk.Label(info_top, text=f"ID: {usuario.id_usuario}",
                 font=("Segoe UI", 8),
                 bg="white", fg="#94a3b8",
                 anchor="w").pack(anchor="w")

        if es_yo_mismo:
            tk.Label(info_top, text="(Tú)",
                     font=("Segoe UI", 8, "italic"),
                     bg="white", fg="#10b981",
                     anchor="w").pack(anchor="w")

        tk.Frame(inner, bg="#e2e8f0", height=1).pack(fill="x", pady=8)

        badge_frame = tk.Frame(inner, bg="white")
        badge_frame.pack(fill="x")

        tk.Label(badge_frame, text="Rol:",
                 font=("Segoe UI", 8),
                 bg="white", fg="#64748b").pack(side="left", padx=(0, 6))

        tk.Label(badge_frame,
                 text=f" {icono_rol} {usuario.rol} ",
                 font=("Segoe UI", 9, "bold"),
                 bg=bg_rol, fg=fg_rol,
                 padx=8, pady=3).pack(side="left")

        tk.Label(inner, text=f"🔑  {usuario.contrasena}",
                 font=("Segoe UI", 9),
                 bg="white", fg="#94a3b8").pack(anchor="w", pady=(6, 0))

        if Usuario.tiene_prestamos_vencidos(usuario.id_usuario):
            tk.Label(inner, text="⚠️  Tiene préstamos vencidos",
                     font=("Segoe UI", 8, "bold"),
                     bg="#fee2e2", fg="#991b1b",
                     padx=6, pady=2).pack(anchor="w", pady=(4, 0))

        botones = tk.Frame(inner, bg="white")
        botones.pack(fill="x", pady=(10, 0))

        tk.Button(botones, text="✏️  Editar",
                  font=("Segoe UI", 8, "bold"),
                  bg="#dbeafe", fg="#1e40af",
                  activebackground="#bfdbfe", activeforeground="#1e40af",
                  bd=0, cursor="hand2", padx=8, pady=4,
                  command=lambda u=usuario: self.abrir_form(u)
                  ).pack(side="left", padx=2)

        tk.Button(botones, text="🔐",
                  font=("Segoe UI Emoji", 9),
                  bg="#e2e8f0", fg="#0f172a",
                  activebackground="#cbd5e1",
                  bd=0, cursor="hand2", padx=8, pady=4,
                  command=lambda u=usuario: self.cambiar_contrasena(u)
                  ).pack(side="left", padx=2)

        if not es_yo_mismo:
            if es_admin:
                tk.Button(botones, text="⬇️ Quitar Admin",
                          font=("Segoe UI", 7, "bold"),
                          bg="#fef3c7", fg="#92400e",
                          activebackground="#fde68a",
                          bd=0, cursor="hand2", padx=6, pady=4,
                          command=lambda u=usuario: self.cambiar_rol(u, "Usuario")
                          ).pack(side="left", padx=2)
            else:
                tk.Button(botones, text="⬆️ Dar Admin",
                          font=("Segoe UI", 7, "bold"),
                          bg="#fef3c7", fg="#92400e",
                          activebackground="#fde68a",
                          bd=0, cursor="hand2", padx=6, pady=4,
                          command=lambda u=usuario: self.cambiar_rol(u, "Admin")
                          ).pack(side="left", padx=2)

            tk.Button(botones, text="🗑️",
                      font=("Segoe UI Emoji", 9),
                      bg="#fee2e2", fg="#991b1b",
                      activebackground="#fecaca", activeforeground="#991b1b",
                      bd=0, cursor="hand2", padx=8, pady=4,
                      command=lambda u=usuario: self.eliminar(u)
                      ).pack(side="right", padx=2)

    def _crear_tarjeta_papelera(self, parent, usuario, fila, columna):
        card = tk.Frame(parent, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.grid(row=fila, column=columna, padx=8, pady=8, sticky="nsew")

        tk.Frame(card, bg="#94a3b8", height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white")
        inner.pack(fill="both", expand=True, padx=15, pady=12)

        top = tk.Frame(inner, bg="white")
        top.pack(fill="x")

        foto_frame = tk.Frame(top, bg="#94a3b8", width=48, height=48)
        foto_frame.pack(side="left")
        foto_frame.pack_propagate(False)

        foto_cargada = False
        if PIL_OK and getattr(usuario, "foto_perfil", None) and \
                os.path.exists(usuario.foto_perfil):
            try:
                img = Image.open(usuario.foto_perfil).convert("RGBA")
                img = img.resize((48, 48), Image.LANCZOS)
                foto_img = ImageTk.PhotoImage(img)

                lbl_foto = tk.Label(foto_frame, image=foto_img, bg="#94a3b8")
                lbl_foto.image = foto_img
                lbl_foto.pack(expand=True)
                foto_cargada = True
            except Exception:
                pass

        if not foto_cargada:
            inicial = usuario.usuario_login[0].upper() if usuario.usuario_login else "?"
            tk.Label(foto_frame, text=inicial,
                     font=("Segoe UI", 18, "bold"),
                     bg="#94a3b8", fg="white").pack(expand=True)

        info_top = tk.Frame(top, bg="white")
        info_top.pack(side="left", padx=(12, 0), fill="x", expand=True)

        tk.Label(info_top, text=usuario.usuario_login,
                 font=("Segoe UI", 12, "bold"),
                 bg="white", fg="#94a3b8",
                 anchor="w").pack(anchor="w")

        tk.Label(info_top, text=f"ID: {usuario.id_usuario}",
                 font=("Segoe UI", 8),
                 bg="white", fg="#cbd5e1",
                 anchor="w").pack(anchor="w")

        tk.Frame(inner, bg="#e2e8f0", height=1).pack(fill="x", pady=8)

        tk.Label(inner, text="🗑️  En papelera",
                 font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#dc2626").pack(anchor="w")

        tk.Label(inner, text=f"Rol anterior: {usuario.rol}",
                 font=("Segoe UI", 8),
                 bg="white", fg="#64748b").pack(anchor="w", pady=(4, 0))

        botones = tk.Frame(inner, bg="white")
        botones.pack(fill="x", pady=(10, 0))

        tk.Button(botones, text="♻️  Restaurar",
                  font=("Segoe UI", 8, "bold"),
                  bg="#d1fae5", fg="#065f46",
                  activebackground="#a7f3d0", activeforeground="#065f46",
                  bd=0, cursor="hand2", padx=8, pady=4,
                  command=lambda u=usuario: self.restaurar(u)
                  ).pack(side="left", padx=2)

        tk.Button(botones, text="❌",
                  font=("Segoe UI Emoji", 9),
                  bg="#fee2e2", fg="#991b1b",
                  activebackground="#fecaca", activeforeground="#991b1b",
                  bd=0, cursor="hand2", padx=8, pady=4,
                  command=lambda u=usuario: self.eliminar_definitivo(u)
                  ).pack(side="right", padx=2)

    def cargar_usuarios(self):
        self._limpiar_tarjetas()
        self.entry_buscar.delete(0, tk.END)

        try:
            if self.mostrando_papelera:
                usuarios = Usuario.obtener_eliminados()
                for i, usuario in enumerate(usuarios):
                    self._crear_tarjeta_papelera(self.frame_usuarios,
                                                 usuario, i // 3, i % 3)
                self.lbl_contador.config(
                    text=f"🗑️  {len(usuarios)} en papelera")
            else:
                usuarios = Usuario.obtener_todos()
                for i, usuario in enumerate(usuarios):
                    self._crear_tarjeta(self.frame_usuarios,
                                        usuario, i // 3, i % 3)
                self.lbl_contador.config(text=f"👥  {len(usuarios)} usuarios")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar:\n\n{e}")

    def buscar(self):
        texto = self.entry_buscar.get().strip().lower()
        if not texto:
            self.cargar_usuarios()
            return

        self._limpiar_tarjetas()

        try:
            if self.mostrando_papelera:
                usuarios = Usuario.obtener_eliminados()
            else:
                usuarios = Usuario.obtener_todos()

            filtrados = [u for u in usuarios if texto in u.usuario_login.lower()]

            for i, usuario in enumerate(filtrados):
                if self.mostrando_papelera:
                    self._crear_tarjeta_papelera(self.frame_usuarios,
                                                 usuario, i // 3, i % 3)
                else:
                    self._crear_tarjeta(self.frame_usuarios,
                                        usuario, i // 3, i % 3)

            self.lbl_contador.config(text=f"🔎  {len(filtrados)} resultado(s)")

            if not filtrados:
                tk.Label(self.frame_usuarios,
                         text="🔎 No se encontraron usuarios",
                         font=("Segoe UI", 12),
                         bg="#f1f5f9", fg="#94a3b8").pack(pady=40)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def abrir_form(self, usuario=None):
        w = tk.Toplevel(self)
        w.title("Nuevo Usuario" if usuario is None else "Editar Usuario")
        w.geometry("480x620")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg="#0f172a")
        header_inner.pack(side="left", padx=20, pady=12)

        icono = "➕" if usuario is None else "✏️"
        titulo = "Nuevo Usuario" if usuario is None else "Editar Usuario"

        tk.Label(header_inner, text=icono,
                 font=("Segoe UI Emoji", 16),
                 bg="#0f172a", fg="#38bdf8").pack(side="left")

        tk.Label(header_inner, text=titulo,
                 font=("Segoe UI", 13, "bold"),
                 bg="#0f172a", fg="#f8fafc").pack(side="left", padx=(8, 0))

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 9, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=14, pady=5,
                  command=w.destroy).pack(side="right", padx=20, pady=15)

        body = tk.Frame(w, bg="#f1f5f9")
        body.pack(fill="both", expand=True, padx=15, pady=10)

        card_datos = tk.Frame(body, bg="white", highlightthickness=1,
                              highlightbackground="#e2e8f0")
        card_datos.pack(fill="x", pady=(0, 8))

        tk.Frame(card_datos, bg="#38bdf8", height=3).pack(fill="x")

        inner_datos = tk.Frame(card_datos, bg="white", padx=18, pady=12)
        inner_datos.pack(fill="x")

        tk.Label(inner_datos, text="👤 Datos del Usuario",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 8))

        tk.Label(inner_datos, text="Usuario:",
                 font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 3))

        entry_login = tk.Entry(inner_datos, width=40,
                               font=("Segoe UI", 10),
                               bg="#f8fafc", bd=1, relief="solid")
        entry_login.pack(fill="x", ipady=4, pady=(0, 8))

        if usuario:
            entry_login.insert(0, usuario.usuario_login)

        tk.Label(inner_datos, text="Rol:",
                 font=("Segoe UI", 9, "bold"),
                 bg="white", fg="#334155").pack(anchor="w", pady=(0, 3))

        combo_rol = ttk.Combobox(inner_datos, width=37, state="readonly",
                                 values=["Usuario", "Admin"],
                                 font=("Segoe UI", 9))
        combo_rol.set(usuario.rol if usuario else "Usuario")
        combo_rol.pack(fill="x", pady=(0, 3))

        yo = self.auth.get_usuario_actual()
        es_yo_mismo = (usuario and yo and usuario.id_usuario == yo.id_usuario)

        if es_yo_mismo:
            combo_rol.config(state="disabled")
            tk.Label(inner_datos,
                     text="⚠️ No puedes cambiar tu propio rol",
                     font=("Segoe UI", 8, "italic"),
                     bg="white", fg="#f59e0b").pack(anchor="w")

        entry_pass_actual = None
        entry_pass_nueva = None
        entry_pass_confirm = None

        if usuario is not None:
            card_pass = tk.Frame(body, bg="white", highlightthickness=1,
                                 highlightbackground="#e2e8f0")
            card_pass.pack(fill="x", pady=(0, 8))

            tk.Frame(card_pass, bg="#f59e0b", height=3).pack(fill="x")

            inner_pass = tk.Frame(card_pass, bg="white", padx=18, pady=12)
            inner_pass.pack(fill="x")

            tk.Label(inner_pass, text="🔐 Cambiar Contraseña",
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#0f172a").pack(anchor="w")

            tk.Label(inner_pass,
                     text="Deja en blanco para no cambiar la contraseña",
                     font=("Segoe UI", 8, "italic"),
                     bg="white", fg="#94a3b8").pack(anchor="w", pady=(0, 8))

            entry_pass_actual = self._campo_password(inner_pass, "Actual:")
            entry_pass_nueva = self._campo_password(inner_pass, "Nueva:")
            entry_pass_confirm = self._campo_password(inner_pass, "Confirmar:")
        else:
            card_pass = tk.Frame(body, bg="white", highlightthickness=1,
                                 highlightbackground="#e2e8f0")
            card_pass.pack(fill="x", pady=(0, 8))

            tk.Frame(card_pass, bg="#10b981", height=3).pack(fill="x")

            inner_pass = tk.Frame(card_pass, bg="white", padx=18, pady=12)
            inner_pass.pack(fill="x")

            tk.Label(inner_pass, text="🔐 Contraseña",
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#0f172a").pack(anchor="w")

            tk.Label(inner_pass,
                     text="Contraseña obligatoria para el nuevo usuario",
                     font=("Segoe UI", 8, "italic"),
                     bg="white", fg="#94a3b8").pack(anchor="w", pady=(0, 8))

            entry_pass_nueva = self._campo_password(inner_pass, "Contraseña:")
            entry_pass_confirm = self._campo_password(inner_pass, "Confirmar:")

        def guardar():
            login = entry_login.get().strip()

            if not login:
                messagebox.showwarning("Campo requerido",
                                       "El usuario es obligatorio.", parent=w)
                entry_login.focus()
                return

            nueva_pass_final = None

            if usuario is not None:
                pass_actual = entry_pass_actual.get().strip()
                pass_nueva = entry_pass_nueva.get().strip()
                pass_confirm = entry_pass_confirm.get().strip()

                if pass_actual or pass_nueva or pass_confirm:
                    if not pass_actual:
                        messagebox.showwarning("Campo requerido",
                                               "Ingresa tu contraseña actual.",
                                               parent=w)
                        entry_pass_actual.focus()
                        return
                    if not pass_nueva:
                        messagebox.showwarning("Campo requerido",
                                               "Ingresa la nueva contraseña.",
                                               parent=w)
                        entry_pass_nueva.focus()
                        return
                    if not pass_confirm:
                        messagebox.showwarning("Campo requerido",
                                               "Confirma la nueva contraseña.",
                                               parent=w)
                        entry_pass_confirm.focus()
                        return
                    if pass_nueva != pass_confirm:
                        messagebox.showwarning(
                            "No coinciden",
                            "La nueva contraseña y la confirmación no coinciden.",
                            parent=w)
                        entry_pass_confirm.delete(0, tk.END)
                        entry_pass_confirm.focus()
                        return
                    if len(pass_nueva) < 6:
                        messagebox.showwarning(
                            "Contraseña débil",
                            "La nueva contraseña debe tener al menos 6 caracteres.",
                            parent=w)
                        entry_pass_nueva.focus()
                        return

                    if pass_actual != usuario.contrasena:
                        messagebox.showerror("Contraseña incorrecta",
                                             "La contraseña actual no es correcta.",
                                             parent=w)
                        entry_pass_actual.delete(0, tk.END)
                        entry_pass_actual.focus()
                        return

                    nueva_pass_final = pass_nueva
            else:
                pass_nueva = entry_pass_nueva.get().strip()
                pass_confirm = entry_pass_confirm.get().strip()

                if not pass_nueva:
                    messagebox.showwarning("Campo requerido",
                                           "La contraseña es obligatoria.",
                                           parent=w)
                    entry_pass_nueva.focus()
                    return
                if not pass_confirm:
                    messagebox.showwarning("Campo requerido",
                                           "Confirma la contraseña.", parent=w)
                    entry_pass_confirm.focus()
                    return
                if pass_nueva != pass_confirm:
                    messagebox.showwarning("No coinciden",
                                           "Las contraseñas no coinciden.",
                                           parent=w)
                    entry_pass_confirm.delete(0, tk.END)
                    entry_pass_confirm.focus()
                    return
                if len(pass_nueva) < 6:
                    messagebox.showwarning(
                        "Contraseña débil",
                        "La contraseña debe tener al menos 6 caracteres.",
                        parent=w)
                    entry_pass_nueva.focus()
                    return

                nueva_pass_final = pass_nueva

            try:
                obj = Usuario() if usuario is None else usuario
                obj.usuario_login = login

                if not es_yo_mismo:
                    obj.rol = combo_rol.get()

                if nueva_pass_final:
                    obj.contrasena = nueva_pass_final

                obj.guardar()
                w.destroy()
                self.cargar_usuarios()

                if usuario is not None and nueva_pass_final:
                    messagebox.showinfo(
                        "Éxito",
                        "✅ Usuario y contraseña actualizados correctamente.")
                else:
                    messagebox.showinfo("Éxito",
                                        "✅ Usuario guardado correctamente.")
            except Exception as e:
                err = str(e)
                if "ya existe" in err:
                    messagebox.showerror("Usuario duplicado", err, parent=w)
                elif "UNIQUE" in err or "duplicate" in err.lower():
                    messagebox.showerror(
                        "Usuario duplicado",
                        f"El usuario '{login}' ya existe.\n\nElige otro nombre.",
                        parent=w)
                else:
                    messagebox.showerror("Error", str(e), parent=w)

        botones_container = tk.Frame(body, bg="#f1f5f9")
        botones_container.pack(fill="x", pady=(4, 0))

        tk.Button(botones_container, text="💾  Guardar Cambios",
                  font=("Segoe UI", 10, "bold"),
                  bg="#10b981", fg="white",
                  activebackground="#059669", activeforeground="white",
                  bd=0, cursor="hand2", padx=30, pady=8,
                  command=guardar).pack()

        entry_login.focus()

    def cambiar_rol(self, usuario, nuevo_rol):
        accion = ("dar permisos de administrador a" if nuevo_rol == "Admin"
                  else "quitar permisos de administrador a")

        if not messagebox.askyesno("Confirmar",
                                   f"¿Seguro que deseas {accion} "
                                   f"'{usuario.usuario_login}'?"):
            return

        try:
            usuario.rol = nuevo_rol
            usuario.guardar()
            self.cargar_usuarios()
            messagebox.showinfo("Éxito", f"✅ Rol actualizado a {nuevo_rol}.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cambiar_contrasena(self, usuario):
        w = tk.Toplevel(self)
        w.title("Cambiar contraseña")
        w.geometry("420x450")
        w.configure(bg="#f1f5f9")
        w.transient(self)
        w.grab_set()
        w.focus_force()
        w.resizable(False, False)
        quitar_boton_cerrar(w)

        header = tk.Frame(w, bg="#0f172a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔐  Cambiar Contraseña",
                 font=("Segoe UI", 13, "bold"), bg="#0f172a",
                 fg="#38bdf8").pack(side="left", padx=20, pady=15)

        tk.Button(header, text="✖  Cerrar",
                  font=("Segoe UI", 9, "bold"),
                  bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, cursor="hand2", padx=14, pady=5,
                  command=w.destroy).pack(side="right", padx=20, pady=13)

        body = tk.Frame(w, bg="white", padx=20, pady=15)
        body.pack(fill="both", expand=True, padx=15, pady=15)

        tk.Label(body, text=f"Usuario: {usuario.usuario_login}",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 12))

        entry_actual = self._campo_password(body, "Contraseña actual:")
        entry_nueva = self._campo_password(body, "Nueva contraseña:")
        entry_confirm = self._campo_password(body, "Confirmar nueva contraseña:")

        entry_actual.focus()

        def guardar():
            actual = entry_actual.get().strip()
            nueva = entry_nueva.get().strip()
            confirm = entry_confirm.get().strip()

            if not actual:
                messagebox.showwarning("Contraseña",
                                       "Ingresa la contraseña actual.", parent=w)
                entry_actual.focus()
                return
            if not nueva:
                messagebox.showwarning("Contraseña",
                                       "Ingresa la nueva contraseña.", parent=w)
                entry_nueva.focus()
                return
            if not confirm:
                messagebox.showwarning("Contraseña",
                                       "Confirma la nueva contraseña.", parent=w)
                entry_confirm.focus()
                return
            if nueva != confirm:
                messagebox.showwarning("No coinciden",
                                       "Las contraseñas no coinciden.", parent=w)
                entry_confirm.delete(0, tk.END)
                entry_confirm.focus()
                return
            if len(nueva) < 6:
                messagebox.showwarning("Contraseña débil",
                                       "La nueva contraseña debe tener al menos 6 caracteres.",
                                       parent=w)
                entry_nueva.focus()
                return

            if actual != usuario.contrasena:
                messagebox.showerror("Contraseña incorrecta",
                                     "La contraseña actual no es correcta.",
                                     parent=w)
                entry_actual.delete(0, tk.END)
                entry_actual.focus()
                return

            usuario.contrasena = nueva
            try:
                usuario.guardar()
                w.destroy()
                messagebox.showinfo("Éxito", "✅ Contraseña actualizada.")
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=w)

        tk.Button(body, text="🔐  Cambiar Contraseña",
                  font=("Segoe UI", 10, "bold"),
                  bg="#38bdf8", fg="#0f172a",
                  activebackground="#0ea5e9", activeforeground="white",
                  bd=0, cursor="hand2", padx=20, pady=8,
                  command=guardar).pack(pady=(8, 0))

    def eliminar(self, usuario):
        if messagebox.askyesno("Mover a papelera",
                               f"¿Mover a la papelera al usuario?\n\n"
                               f"👤 {usuario.usuario_login}\n"
                               f"🎫 Rol: {usuario.rol}\n\n"
                               f"Podrás restaurarlo después."):
            try:
                usuario.eliminar()
                self.cargar_usuarios()
                messagebox.showinfo("Éxito",
                                    "🗑️ Usuario movido a la papelera.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def restaurar(self, usuario):
        try:
            usuario.restaurar()
            self.cargar_usuarios()
            messagebox.showinfo("Éxito", "♻️ Usuario restaurado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_definitivo(self, usuario):
        if messagebox.askyesno("Eliminar definitivamente",
                               f"⚠️ ¿Eliminar PERMANENTEMENTE a "
                               f"'{usuario.usuario_login}'?\n\n"
                               f"Esta acción NO se puede deshacer.",
                               icon="warning"):
            try:
                usuario.eliminar_definitivo()
                self.cargar_usuarios()
                messagebox.showinfo("Éxito",
                                    "❌ Usuario eliminado definitivamente.")
            except Exception as e:
                messagebox.showerror("Error", str(e))