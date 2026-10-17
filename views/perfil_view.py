import os
import tkinter as tk
from tkinter import filedialog, messagebox

from models import Usuario
from auth_manager import AuthManager

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


class PerfilView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f1f5f9")
        self.auth = AuthManager()
        self._build_ui()

    def on_show(self):
        self.cargar_perfil()

    def _build_ui(self):
        self.body = tk.Frame(self, bg="#f1f5f9")
        self.body.pack(fill="both", expand=True, padx=20, pady=20)

    def cargar_perfil(self):
        for w in self.body.winfo_children():
            w.destroy()

        u = self.auth.get_usuario_actual()
        if not u:
            return

        self._crear_header(u)
        self._crear_datos(u)

    def _crear_header(self, u):
        card = tk.Frame(self.body, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.pack(fill="x", pady=(0, 12))

        tk.Frame(card, bg="#1e3a8a", height=4).pack(fill="x")

        inner = tk.Frame(card, bg="white", padx=20, pady=15)
        inner.pack(fill="x")

        foto_frame = tk.Frame(inner, bg="#1e3a8a", width=80, height=80)
        foto_frame.pack(side="left")
        foto_frame.pack_propagate(False)

        foto_cargada = False
        if u.foto_perfil and os.path.exists(u.foto_perfil) and PIL_OK:
            try:
                img = Image.open(u.foto_perfil).convert("RGBA")
                img = img.resize((80, 80), Image.LANCZOS)
                foto_img = ImageTk.PhotoImage(img)
                lbl = tk.Label(foto_frame, image=foto_img, bg="#1e3a8a")
                lbl.image = foto_img
                lbl.pack(expand=True)
                foto_cargada = True
            except Exception:
                pass

        if not foto_cargada:
            inicial = u.usuario_login[0].upper() if u.usuario_login else "?"
            tk.Label(foto_frame, text=inicial,
                     font=("Segoe UI", 32, "bold"),
                     bg="#1e3a8a", fg="white").pack(expand=True)

        info = tk.Frame(inner, bg="white")
        info.pack(side="left", padx=(20, 0), fill="x", expand=True)

        tk.Label(info, text=u.usuario_login,
                 font=("Segoe UI", 18, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w")

        rol_icono = "👑 ADMIN" if u.rol == "Admin" else "👤 USUARIO"
        rol_color = "#ef4444" if u.rol == "Admin" else "#3b82f6"
        tk.Label(info, text=rol_icono,
                 font=("Segoe UI", 9, "bold"),
                 bg="white", fg=rol_color).pack(anchor="w", pady=(6, 0))

        botones_foto = tk.Frame(inner, bg="white")
        botones_foto.pack(side="right", pady=2)

        texto_boton = "Cambiar Foto de Perfil" if foto_cargada else "Agregar Foto de Perfil"

        tk.Button(botones_foto, text=texto_boton,
                  font=("Segoe UI", 10, "bold"),
                  bg="#dbeafe", fg="#1e40af",
                  activebackground="#bfdbfe", activeforeground="#1e40af",
                  bd=0, cursor="hand2", padx=15, pady=8,
                  command=lambda: self.cambiar_foto(u)
                  ).pack(side="top", pady=(0, 4))

        if foto_cargada:
            tk.Button(botones_foto, text="Quitar Foto",
                      font=("Segoe UI", 10, "bold"),
                      bg="#fee2e2", fg="#991b1b",
                      activebackground="#fecaca", activeforeground="#991b1b",
                      bd=0, cursor="hand2", padx=15, pady=8,
                      command=lambda: self.quitar_foto(u)
                      ).pack(side="top")

    def cambiar_foto(self, u):
        archivo = filedialog.askopenfilename(
            title="Selecciona tu nueva foto de perfil",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg")]
        )
        if not archivo:
            return

        try:
            u.foto_perfil = archivo
            u.guardar()
            messagebox.showinfo("Éxito", " Foto de perfil actualizada.")
            self.cargar_perfil()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar:\n\n{e}")

    def quitar_foto(self, u):
        if not messagebox.askyesno(
                "Quitar Foto",
                "¿Estás seguro de que deseas quitar tu foto de perfil?\n\n"
                "Se mostrará tu inicial como avatar."):
            return

        try:
            u.foto_perfil = None
            u.guardar()
            messagebox.showinfo("Éxito", " Foto de perfil eliminada.")
            self.cargar_perfil()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo quitar la foto:\n\n{e}")

    def _crear_datos(self, u):
        card = tk.Frame(self.body, bg="white", highlightthickness=1,
                        highlightbackground="#e2e8f0")
        card.pack(fill="x", pady=(0, 15))

        inner = tk.Frame(card, bg="white", padx=20, pady=18)
        inner.pack(fill="x")

        tk.Label(inner, text="Información Personal",
                 font=("Segoe UI", 13, "bold"),
                 bg="white", fg="#0f172a").pack(anchor="w", pady=(0, 12))

        def fila(label, valor):
            f = tk.Frame(inner, bg="white")
            f.pack(fill="x", pady=6)

            tk.Label(f, text=label,
                     font=("Segoe UI", 10, "bold"),
                     bg="white", fg="#64748b",
                     width=14, anchor="w").pack(side="left")

            tk.Label(f, text=str(valor) if valor else "—",
                     font=("Segoe UI", 10),
                     bg="white", fg="#0f172a", anchor="w").pack(side="left")

        fila("ID:", u.id_usuario)
        fila("Usuario:", u.usuario_login)
        fila("Rol:", u.rol)