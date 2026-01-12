from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QHBoxLayout, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt

class TabHistorial(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()
        
        # Cargar datos automáticamente al iniciar
        self.cargar_datos()

    def initUI(self):
        layout = QVBoxLayout()

        # --- 1. Botonera Superior ---
        btn_layout = QHBoxLayout()
        
        btn_refresh = QPushButton("🔄 Actualizar Tabla")
        btn_refresh.clicked.connect(self.cargar_datos)
        btn_layout.addWidget(btn_refresh)

        btn_delete = QPushButton("🗑️ Eliminar Fila Seleccionada")
        btn_delete.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        btn_delete.clicked.connect(self.borrar_fila)
        btn_layout.addWidget(btn_delete)
        
        layout.addLayout(btn_layout)
        
        # --- 2. Tabla ---
        self.tabla = QTableWidget()
        # Configuración para seleccionar filas completas
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # No editable directo
        
        cols = ["Fecha", "Resp", "Cliente", "Modelo", "Tipo", "Material", "Color", "Peso", "Tiempo", "Cant", "Diseño", "Total", "Unitario"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        
        # Estética de columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.tabla)
        self.setLayout(layout)

    def cargar_datos(self):
        """Descarga el historial de Drive y rellena la tabla"""
        datos_brutos = self.backend.obtener_historial_completo()
        
        # Limpiar tabla actual
        self.tabla.setRowCount(0)
        
        if not datos_brutos:
            return

        # Asumimos que la primera fila es el encabezado en Drive, la saltamos
        filas_datos = datos_brutos[1:] 

        self.tabla.setRowCount(len(filas_datos))
        
        for i, fila in enumerate(filas_datos):
            for j, valor in enumerate(fila):
                # Protección por si la fila tiene menos columnas
                if j < self.tabla.columnCount():
                    item = QTableWidgetItem(str(valor))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tabla.setItem(i, j, item)

    def borrar_fila(self):
        """Lógica para borrar"""
        filas_seleccionadas = self.tabla.selectionModel().selectedRows()
        
        if not filas_seleccionadas:
            QMessageBox.warning(self, "Alerta", "Por favor selecciona una fila para borrar.")
            return

        # Obtenemos el índice visual (0, 1, 2...)
        indice = filas_seleccionadas[0].row()
        
        # Confirmación de seguridad
        confirmacion = QMessageBox.question(
            self, "Confirmar Borrado", 
            "¿Estás seguro de que quieres borrar este registro permanentemente de Google Drive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirmacion == QMessageBox.StandardButton.Yes:
            # Llamamos al backend
            exito = self.backend.borrar_fila_historial(indice)
            
            if exito:
                QMessageBox.information(self, "Listo", "Fila eliminada correctamente.")
                self.cargar_datos() # Recargamos para ver el cambio
            else:
                QMessageBox.critical(self, "Error", "No se pudo borrar la fila en Drive. Revisa tu conexión.")