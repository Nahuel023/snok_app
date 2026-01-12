# tabs/llaveros.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox, 
    QPushButton, QHBoxLayout, QTextEdit, QLabel, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

class TabLlaveros(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        # 1. Layout Principal (Horizontal para centrar el formulario en el medio de la pantalla)
        main_layout = QHBoxLayout()
        
        # 2. Contenedor Central (La "Tarjeta")
        # Creamos un widget contenedor para limitar el ancho y que no se estire infinito
        card_widget = QWidget()
        card_widget.setMaximumWidth(550)  # Ancho máximo ideal para formularios
        
        layout = QVBoxLayout(card_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Pegar todo arriba
        layout.setSpacing(15) # Espacio vertical moderado entre elementos

        # --- Título / Info ---
        info_box = QLabel("💡 Venta rápida (stock/reventa)")
        info_box.setStyleSheet("color: #888; font-style: italic; font-size: 12px;")
        info_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_box)

        # --- FORMULARIO COMPACTO ---
        group_form = QGroupBox("Datos de la Venta")
        group_form.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 10px; }")
        
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # Etiquetas alineadas a la derecha
        form.setContentsMargins(20, 20, 20, 20) # Márgenes internos cómodos
        form.setVerticalSpacing(12) # Espacio entre renglones

        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Nombre...")
        form.addRow("👤 Cliente:", self.input_cliente)

        self.input_modelo = QLineEdit()
        self.input_modelo.setPlaceholderText("Producto...")
        form.addRow("📦 Producto:", self.input_modelo)

        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 10000); self.spin_cantidad.setValue(1)
        form.addRow("#️⃣ Cantidad:", self.spin_cantidad)

        self.spin_precio_unit = QSpinBox()
        self.spin_precio_unit.setRange(0, 1000000); self.spin_precio_unit.setPrefix("$ "); self.spin_precio_unit.setValue(500)
        form.addRow("💲 Precio Unit.:", self.spin_precio_unit)

        group_form.setLayout(form)
        layout.addWidget(group_form)

        # --- BOTONES (Más compactos y estéticos) ---
        h_bots = QHBoxLayout()
        
        btn_calc = QPushButton("CALCULAR")
        btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calc.setMinimumHeight(35)
        btn_calc.clicked.connect(self.calcular)
        h_bots.addWidget(btn_calc)

        btn_save = QPushButton("REGISTRAR")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setMinimumHeight(35)
        btn_save.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; border-radius: 4px;")
        btn_save.clicked.connect(self.guardar)
        h_bots.addWidget(btn_save)

        layout.addLayout(h_bots)

        # --- RESULTADO (Caja pequeña) ---
        self.txt_res = QTextEdit()
        self.txt_res.setReadOnly(True)
        self.txt_res.setMaximumHeight(60) # Altura reducida
        self.txt_res.setPlaceholderText("El total aparecerá aquí...")
        self.txt_res.setStyleSheet("""
            background-color: #2b2b2b; 
            color: #ecf0f1; 
            border: 1px solid #555; 
            border-radius: 5px; 
            padding: 5px;
        """)
        layout.addWidget(self.txt_res)
        
        layout.addStretch() # Empuja todo hacia arriba si sobra espacio vertical

        # 3. Ensamblaje Final: Centrar el card_widget en la ventana
        main_layout.addStretch() # Resorte Izquierda
        main_layout.addWidget(card_widget) # Contenido Centro
        main_layout.addStretch() # Resorte Derecha
        
        self.setLayout(main_layout)

    def calcular(self):
        try:
            cant = self.spin_cantidad.value()
            unitario = self.spin_precio_unit.value()
            total = cant * unitario

            # Mensaje corto y claro
            msg = f"✅ Total: {cant} x ${unitario} = ${total:,.2f}"
            self.txt_res.setText(msg)
            return total
        except:
            self.txt_res.setText("Error cálculo")
            return 0

    def guardar(self):
        total = self.calcular()
        
        if total > 0:
            if not self.input_cliente.text():
                QMessageBox.warning(self, "Error", "Falta el nombre del cliente.")
                return

            cli = self.input_cliente.text()
            mod = self.input_modelo.text() or "Varios"
            fecha = datetime.now().strftime("%d/%m/%Y")
            cant = self.spin_cantidad.value()
            unitario = self.spin_precio_unit.value()

            fila = [
                fecha,          # Fecha
                "Usuario",      # Resp
                cli,            # Cliente
                mod,            # Modelo
                "Venta Directa",# Tipo
                "-",            # Material
                "-",            # Color
                "0",            # Peso
                "N/A",          # Tiempo
                cant,           # Cant
                "-",            # Diseño
                f"${total:.2f}",   # Total
                f"${unitario:.2f}" # Unitario
            ]

            ok = self.backend.guardar_fila_historial(fila)
            
            if ok:
                QMessageBox.information(self, "Registrado", "✅ Venta registrada.")
                self.input_modelo.clear()
                self.spin_cantidad.setValue(1)
                self.txt_res.clear()
            else:
                QMessageBox.critical(self, "Error", "❌ Falló conexión con Drive.")