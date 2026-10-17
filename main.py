import os
import ctypes
import threading
import tkinter as tk

from database import get_connection
from auth_manager import AuthManager
from views.login_view import LoginView
from views.dashboard_view import DashboardView

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


class AppContainer(tk.Tk):
    def __init__(self):
        super().__init__()

        self._cargar_icono_ventana()
        self.title("Sistema de Biblioteca")
        self.state('zoomed')
        self.configure(bg="#ffffff")

        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(fill="both", expand=True)
        self.container.pack_propagate(False)

        self.lbl_cargando = tk.Label(
            self.container,
            text="📚  Cargando Sistema...",
            font=("Segoe UI", 22, "bold"),
            bg="#ffffff",
            fg="#1e3a8a"
        )
        self.lbl_cargando.pack(expand=True)

        self.after(200, self.quitar_botones_titulo)

        threading.Thread(target=self._iniciar_sistema, daemon=True).start()

    def _iniciar_sistema(self):
        try:
            conn = get_connection()
            conn.close()
        except Exception:
            pass

        self.after(0, self._mostrar_login)

    def _mostrar_login(self):
        self.lbl_cargando.destroy()

        self.auth = AuthManager()
        self.auth.set_container(self.container)

        self.auth.registrar_vista_lazy(
            "dashboard",
            lambda parent: DashboardView(parent)
        )

        self.login_view = LoginView(self.container)
        self.login_view.pack(fill="both", expand=True)
        self.auth.vistas["login"] = self.login_view

    def _cargar_icono_ventana(self):
        try:
            try:
                myappid = 'universidad.uni.biblioteca.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

            base_dir = os.path.dirname(os.path.abspath(__file__))
            rutas = [
                os.path.join(base_dir, "logo_unai.ico"),
                os.path.join(base_dir, "logo_unai.png"),
                os.path.join(base_dir, "logo_unai.jpeg"),
                os.path.join(base_dir, "logo_unai.jpg"),
            ]
            ruta_logo = next((r for r in rutas if os.path.exists(r)), None)

            if not ruta_logo:
                return

            if ruta_logo.lower().endswith(".ico"):
                try:
                    self.iconbitmap(ruta_logo)
                    return
                except Exception:
                    pass

            if PIL_OK:
                img = Image.open(ruta_logo).convert("RGBA")
                img = img.resize((32, 32), Image.LANCZOS)

                fondo = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
                x = (32 - img.width) // 2
                y = (32 - img.height) // 2
                fondo.paste(img, (x, y), img)

                self.icono_img = ImageTk.PhotoImage(fondo)
                self.iconphoto(True, self.icono_img)
            else:
                if ruta_logo.lower().endswith(".png"):
                    try:
                        self.icono_img = tk.PhotoImage(file=ruta_logo)
                        self.iconphoto(True, self.icono_img)
                    except Exception:
                        pass
        except Exception:
            pass

    def mostrar_login(self):
        for nombre in list(self.auth.vistas.keys()):
            try:
                self.auth.vistas[nombre].destroy()
            except Exception:
                pass
            del self.auth.vistas[nombre]

        for widget in self.container.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        self.auth.usuario_actual = None

        self.login_view = LoginView(self.container)
        self.login_view.pack(fill="both", expand=True)
        self.auth.vistas["login"] = self.login_view

    def quitar_botones_titulo(self):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            GWL_STYLE = -16
            estilo = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)

            WS_SYSMENU = 0x00080000
            WS_MINIMIZEBOX = 0x00020000
            WS_MAXIMIZEBOX = 0x00010000

            estilo &= ~WS_SYSMENU
            estilo &= ~WS_MINIMIZEBOX
            estilo &= ~WS_MAXIMIZEBOX
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


if __name__ == "__main__":
    app = AppContainer()
    app.mainloop()