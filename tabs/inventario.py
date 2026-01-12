from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, 
    QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox, 
    QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QAbstractItemView
)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt
from datetime import datetime

class TabInventario(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # --- 1. FORMULARIO DE CARGA ---
        group_add = QGroupBox("➕ Alta de Material")
        group_add.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 10px; }")
        
        row1 = QHBoxLayout()
        self.combo_marca = QComboBox(); self.combo_marca.setEditable(True)
        self.combo_marca.addItems(["Elegoo", "BambuLab", "Grilon", "Printalot", "Hellbot", "Generic"])
        self.combo_marca.setPlaceholderText("Marca...")
        
        self.combo_tipo = QComboBox(); self.combo_tipo.setEditable(True)
        self.combo_tipo.addItems(["PLA", "PETG", "ABS", "TPU", "ASA", "Resina"])
        
        row1.addWidget(QLabel("Marca:"))
        row1.addWidget(self.combo_marca)
        row1.addWidget(QLabel("Material:"))
        row1.addWidget(self.combo_tipo)
        
        row2 = QHBoxLayout()
        self.input_color = QLineEdit()
        self.input_color.setPlaceholderText("Ej: Rojo Fuego, Negro...")
        
        self.chk_matte = QCheckBox("Es Matte / Seda")
        
        row2.addWidget(QLabel("Color:"))
        row2.addWidget(self.input_color)
        row2.addWidget(self.chk_matte)

        row3 = QHBoxLayout()
        self.spin_peso = QSpinBox(); self.spin_peso.setRange(0, 10000); self.spin_peso.setValue(1000); self.spin_peso.setSuffix(" g")
        self.spin_precio = QSpinBox(); self.spin_precio.setRange(0, 500000); self.spin_precio.setValue(20000); self.spin_precio.setPrefix("$ ")
        
        row3.addWidget(QLabel("Peso Inicial:"))
        row3.addWidget(self.spin_peso)
        row3.addWidget(QLabel("Costo Rollo:"))
        row3.addWidget(self.spin_precio)

        btn_add = QPushButton("GUARDAR EN STOCK 💾")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 8px;")
        btn_add.clicked.connect(self.agregar_stock)

        form_layout = QVBoxLayout()
        form_layout.addLayout(row1)
        form_layout.addLayout(row2)
        form_layout.addLayout(row3)
        form_layout.addWidget(btn_add)
        
        group_add.setLayout(form_layout)
        layout.addWidget(group_add)

        # --- 2. BARRA DE HERRAMIENTAS ---
        h_tools = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Sincronizar con Nube")
        btn_refresh.clicked.connect(self.descargar_y_actualizar) # Conectado a la nueva función de recarga
        h_tools.addWidget(btn_refresh)
        h_tools.addStretch()
        layout.addLayout(h_tools)

        # --- 3. TABLA ---
        self.tabla = QTableWidget()
        # Nuevas columnas para mostrar estado real
        cols = ["Marca", "Material", "Color", "Peso Restante", "Estado"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.tabla)

        self.setLayout(layout)
        self.actualizar_tabla()

    def agregar_stock(self):
        marca = self.combo_marca.currentText().strip()
        tipo = self.combo_tipo.currentText().strip()
        color = self.input_color.text().strip()
        
        if not color:
            QMessageBox.warning(self, "Faltan datos", "Por favor escribe el color del filamento.")
            return

        acabado = "Matte" if self.chk_matte.isChecked() else "Normal"
        peso = self.spin_peso.value()
        precio = self.spin_precio.value()
        fecha = datetime.now().strftime("%d/%m/%Y")

        # DATOS PARA DRIVE: Enviamos Peso dos veces (Inicial y Actual al principio son iguales)
        # El ID lo pone el backend al principio
        fila_drive = [fecha, marca, tipo, color, acabado, peso, peso, precio]
        
        ok = self.backend.agregar_stock_nube(fila_drive)

        if ok: 
            QMessageBox.information(self, "Éxito", "✅ Rollo agregado correctamente.")
            self.input_color.clear()
            self.chk_matte.setChecked(False)
        else: 
            QMessageBox.warning(self, "Alerta", "⚠️ Se guardó en memoria pero falló Google Drive.")

        self.actualizar_tabla()

    def descargar_y_actualizar(self):
        """Fuerza la descarga de datos reales desde Drive"""
        self.tabla.setDisabled(True)
        ok = self.backend.forzar_descarga_inventario()
        if ok:
            self.actualizar_tabla()
            QMessageBox.information(self, "Sync", "Inventario actualizado desde la nube.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo conectar a Drive.")
        self.tabla.setDisabled(False)

    def actualizar_tabla(self):
        self.tabla.setRowCount(0)
        
        bg_par = QColor("#2b2b2b")
        bg_impar = QColor("#3a3a3a")
        txt_color = QBrush(QColor("white"))

        for item in self.backend.inventario:
            if not isinstance(item, dict): continue

            # Extraer datos seguros
            marca = item.get("Marca") or item.get("marca") or "-"
            tipo = item.get("Tipo") or item.get("tipo") or "-"
            col = item.get("Color") or item.get("color") or "-"
            
            # Pesos
            try:
                p_ini = float(item.get("Peso_Inicial") or 0)
                p_act = float(item.get("Peso_Actual") or p_ini) # Si no existe actual, asumimos lleno
            except:
                p_ini, p_act = 1000, 1000

            # Lógica de Estado (Semáforo)
            porcentaje = (p_act / p_ini * 100) if p_ini > 0 else 0
            estado_txt = "🟢 Lleno"
            if porcentaje < 50: estado_txt = "🟡 Medio"
            if porcentaje < 20: estado_txt = "🔴 Poco"
            if p_act <= 0: estado_txt = "⚫ Vacío"

            vals = [
                marca,
                tipo,
                col,
                f"{int(p_act)}g / {int(p_ini)}g",
                estado_txt
            ]

            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            for i, val in enumerate(vals):
                celda = QTableWidgetItem(str(val))
                celda.setForeground(txt_color)
                if row % 2 == 0: celda.setBackground(bg_par)
                else: celda.setBackground(bg_impar)
                
                if i >= 3: # Centrar peso y estado
                    celda.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                self.tabla.setItem(row, i, celda)