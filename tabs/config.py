from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QSpinBox, QDoubleSpinBox, 
    QPushButton, QMessageBox, QGroupBox, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt

class TabConfig(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        # 1. Layout Principal (Centrado)
        main_layout = QHBoxLayout()
        
        # 2. Tarjeta Central
        card = QGroupBox("⚙️ Ajustes Generales")
        card.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; margin-top: 10px; }")
        card.setMaximumWidth(500) # Ancho controlado
        
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)

        # Formulario
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setContentsMargins(10, 20, 10, 20)

        # Cargamos datos
        cfg = self.backend.configuracion

        # Campos
        self.spin_kwh = QDoubleSpinBox()
        self.spin_kwh.setRange(0, 10000); self.spin_kwh.setPrefix("$ ")
        self.spin_kwh.setValue(float(cfg.get("precio_kwh", 170)))
        form.addRow("Precio Luz (KWh):", self.spin_kwh)

        self.spin_consumo = QDoubleSpinBox()
        self.spin_consumo.setRange(0, 5); self.spin_consumo.setSingleStep(0.01); self.spin_consumo.setSuffix(" kW")
        self.spin_consumo.setValue(float(cfg.get("consumo_kw", 0.2)))
        form.addRow("Consumo Impresora:", self.spin_consumo)

        self.spin_ganancia = QSpinBox()
        self.spin_ganancia.setRange(0, 1000); self.spin_ganancia.setSuffix(" %")
        self.spin_ganancia.setValue(int(cfg.get("margen_ganancia", 100)))
        form.addRow("Margen Ganancia:", self.spin_ganancia)

        self.spin_desgaste = QSpinBox()
        self.spin_desgaste.setRange(0, 50000); self.spin_desgaste.setPrefix("$ ")
        self.spin_desgaste.setValue(int(cfg.get("precio_desgaste_hora", 200)))
        form.addRow("Desgaste Máquina (/h):", self.spin_desgaste)
        
        self.spin_hora_diseno = QSpinBox()
        self.spin_hora_diseno.setRange(0, 100000); self.spin_hora_diseno.setPrefix("$ ")
        self.spin_hora_diseno.setValue(int(cfg.get("precio_hora_diseno", 8500)))
        form.addRow("Hora de Diseño:", self.spin_hora_diseno)

        card_layout.addLayout(form)

        # Botón Guardar
        btn_save = QPushButton("GUARDAR CAMBIOS 💾")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; font-size: 12px;")
        btn_save.clicked.connect(self.guardar_config)
        
        card_layout.addWidget(btn_save)
        
        # Nota al pie
        lbl_note = QLabel("Nota: Estos valores se usan por defecto en el Cotizador.")
        lbl_note.setStyleSheet("color: gray; font-size: 11px;")
        lbl_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_note)

        card.setLayout(card_layout)

        # Ensamblaje
        main_layout.addStretch()
        main_layout.addWidget(card)
        main_layout.addStretch()
        
        self.setLayout(main_layout)

    def guardar_config(self):
        self.backend.configuracion["precio_kwh"] = self.spin_kwh.value()
        self.backend.configuracion["consumo_kw"] = self.spin_consumo.value()
        self.backend.configuracion["margen_ganancia"] = self.spin_ganancia.value()
        self.backend.configuracion["precio_desgaste_hora"] = self.spin_desgaste.value()
        self.backend.configuracion["precio_hora_diseno"] = self.spin_hora_diseno.value()

        if self.backend.save_local_config():
            QMessageBox.information(self, "Éxito", "Configuración actualizada correctamente.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo escribir el archivo JSON.")