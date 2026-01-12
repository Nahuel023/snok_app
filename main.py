# main.py
import sys
import os # Importante para rutas
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtGui import QIcon

# --- BLOQUE DE SEGURIDAD PARA EL TEMA ---
try:
    import qdarktheme
    HAS_THEME = True
except ImportError:
    HAS_THEME = False
# ----------------------------------------

# Importaciones Locales
# Si esto falla, revisa que backend.py esté en la misma carpeta que main.py
try:
    from backend import BackendGestor
    from tabs.cotizador import TabCotizador
    from tabs.inventario import TabInventario
    from tabs.historial import TabHistorial
    from tabs.config import TabConfig
    from tabs.llaveros import TabLlaveros
except ImportError as e:
    print(f"❌ ERROR CRÍTICO DE IMPORTACIÓN: {e}")
    print("Asegúrate de que la carpeta 'tabs' existe y tiene el archivo '__init__.py' dentro.")
    sys.exit(1)

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión Impresión 3D v2.0")
        self.setGeometry(100, 100, 1100, 750)
        
        if os.path.exists("icono.png"):
            self.setWindowIcon(QIcon("icono.png"))

        # 1. INICIAR BACKEND (Cerebro)
        self.backend = BackendGestor() 

        # 2. INTERFAZ PRINCIPAL
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Encabezado
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("<h2>🚀 Panel de Control 3D</h2>"))
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # 3. SISTEMA DE PESTAÑAS
        self.tabs = QTabWidget()
        
        # Instanciar pestañas pasando el 'backend'
        self.tab_cotizador = TabCotizador(self.backend)
        self.tab_inventario = TabInventario(self.backend)
        self.tab_llaveros = TabLlaveros(self.backend)
        self.tab_historial = TabHistorial(self.backend)
        self.tab_config = TabConfig(self.backend)

        # Agregar pestañas
        self.tabs.addTab(self.tab_cotizador, "🖨️ Cotizador")
        self.tabs.addTab(self.tab_inventario, "📦 Stock")
        self.tabs.addTab(self.tab_llaveros, "🔑 Llaveros")
        self.tabs.addTab(self.tab_historial, "📋 Historial")
        self.tabs.addTab(self.tab_config, "⚙️ Config")

        layout.addWidget(self.tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
 
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())