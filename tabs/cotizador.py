from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, 
    QComboBox, QLabel, QSpinBox, QHBoxLayout, QCheckBox, 
    QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from datetime import datetime

class TabCotizador(QWidget):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # --- 1. DATOS DEL CLIENTE ---
        group_cli = QGroupBox("👤 Datos del Cliente")
        form_cli = QFormLayout()
        self.input_cliente = QLineEdit()
        self.input_cliente.setPlaceholderText("Nombre del cliente...")
        self.input_modelo = QLineEdit()
        self.input_modelo.setPlaceholderText("Nombre de la pieza...")
        form_cli.addRow("Cliente:", self.input_cliente)
        form_cli.addRow("Modelo:", self.input_modelo)
        group_cli.setLayout(form_cli)
        layout.addWidget(group_cli)

        # --- 2. MATERIAL (Conectado al Stock) ---
        group_mat = QGroupBox("🧶 Material y Stock")
        layout_mat = QFormLayout()
        
        # A. Crear el Combo y Botón
        h_stock = QHBoxLayout()
        self.combo_stock = QComboBox()
        self.combo_stock.addItem("--- Seleccionar del Inventario ---", None)
        
        btn_refresh_stock = QPushButton("🔄")
        btn_refresh_stock.setFixedWidth(40)
        btn_refresh_stock.setToolTip("Recargar Stock Nube")
        btn_refresh_stock.clicked.connect(self.refrescar_stock_nube)
        
        h_stock.addWidget(self.combo_stock)
        h_stock.addWidget(btn_refresh_stock)
        
        layout_mat.addRow("Stock Disponible:", h_stock)
        
        # B. Crear la etiqueta de Info (IMPORTANTE: Crear antes de llenar datos)
        self.lbl_info = QLabel("Selecciona un material para ver detalles...")
        self.lbl_info.setStyleSheet("color: gray; font-size: 11px;")
        layout_mat.addRow("", self.lbl_info) 

        # C. Conectar señales y cargar datos
        self.combo_stock.currentIndexChanged.connect(self.al_seleccionar_stock)
        self.actualizar_combo_stock()

        # D. Costo Reposición
        self.spin_precio_kg = QSpinBox()
        self.spin_precio_kg.setRange(0, 1000000)
        self.spin_precio_kg.setPrefix("$ ")
        self.spin_precio_kg.setSuffix(" /kg")
        self.spin_precio_kg.setSingleStep(500)
        layout_mat.addRow("Costo de Reposición:", self.spin_precio_kg)
        
        group_mat.setLayout(layout_mat)
        layout.addWidget(group_mat)

        # --- 3. PARÁMETROS TÉCNICOS ---
        group_tech = QGroupBox("⚙️ Parámetros de Impresión")
        layout_tech = QFormLayout()
        
        self.input_peso = QLineEdit()
        self.input_peso.setPlaceholderText("Gramos (con soportes)")
        layout_tech.addRow("Peso Total (g):", self.input_peso)

        h_time = QHBoxLayout()
        self.spin_h = QSpinBox(); self.spin_h.setSuffix(" h"); self.spin_h.setRange(0, 999)
        self.spin_m = QSpinBox(); self.spin_m.setSuffix(" m"); self.spin_m.setRange(0, 59)
        h_time.addWidget(self.spin_h); h_time.addWidget(self.spin_m)
        layout_tech.addRow("Tiempo de Impresión:", h_time)

        self.spin_cant = QSpinBox()
        self.spin_cant.setValue(1); self.spin_cant.setRange(1, 10000)
        layout_tech.addRow("Cantidad de Piezas:", self.spin_cant)
        
        group_tech.setLayout(layout_tech)
        layout.addWidget(group_tech)

        # --- 4. EXTRAS Y DISEÑO ---
        group_extra = QGroupBox("🎨 Extras y Diseño")
        layout_extra = QHBoxLayout()

        self.spin_margen = QSpinBox()
        self.spin_margen.setValue(0) 
        self.spin_margen.setSuffix("%")
        self.spin_margen.setPrefix("Fallo: ")
        layout_extra.addWidget(self.spin_margen)

        self.chk_diseno = QCheckBox("Incluir Diseño")
        self.spin_hs_diseno = QSpinBox()
        self.spin_hs_diseno.setSuffix(" hs")
        self.spin_hs_diseno.setEnabled(False) 
        self.chk_diseno.toggled.connect(lambda: self.spin_hs_diseno.setEnabled(self.chk_diseno.isChecked()))

        layout_extra.addWidget(self.chk_diseno)
        layout_extra.addWidget(self.spin_hs_diseno)

        group_extra.setLayout(layout_extra)
        layout.addWidget(group_extra)

        # --- 5. BOTONES ---
        btn_layout = QHBoxLayout()
        btn_calc = QPushButton("CALCULAR COSTO 🧮")
        btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calc.clicked.connect(self.calcular)
        btn_layout.addWidget(btn_calc)

        btn_save = QPushButton("GUARDAR 💾")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

        # AUMENTADO EL TAMAÑO DE LA CAJA DE TEXTO PARA VER EL DETALLE
        self.txt_res = QTextEdit()
        self.txt_res.setReadOnly(True)
        self.txt_res.setMaximumHeight(200) 
        self.txt_res.setStyleSheet("font-size: 13px; background-color: #2b2b2b; color: white; border: 1px solid #555;")
        layout.addWidget(self.txt_res)

        self.setLayout(layout)

    # --- LÓGICA ---
    def refrescar_stock_nube(self):
        self.backend.forzar_descarga_inventario()
        self.actualizar_combo_stock()
        QMessageBox.information(self, "OK", "Stock actualizado.")

    def actualizar_combo_stock(self):
        self.combo_stock.clear()
        self.combo_stock.addItem("--- Manual / Sin Stock ---", None)
        
        if not self.backend.inventario: return

        for item in self.backend.inventario:
            # Recuperar datos con seguridad
            marca = item.get("Marca") or item.get("marca") or "Gen"
            tipo = item.get("Tipo") or item.get("tipo") or "MAT"
            col = item.get("Color") or item.get("color") or ""
            id_rollo = item.get("ID") 
            
            try:
                p_rollo = float(str(item.get("Precio_Rollo") or 0).replace(',', '.'))
                p_ini = float(str(item.get("Peso_Inicial") or 1000).replace(',', '.'))
                p_act = float(str(item.get("Peso_Actual") or p_ini).replace(',', '.'))
            except:
                p_rollo, p_ini, p_act = 0, 1000, 1000
            
            if p_act < 5: continue 
            
            txt = f"{marca} {tipo} - {col} ({int(p_act)}g disp.)"
            
            data = {
                "id": id_rollo,
                "precio_rollo": p_rollo, 
                "peso_ini": p_ini,
                "peso_act": p_act,
                "desc": txt
            }
            self.combo_stock.addItem(txt, data)

    def al_seleccionar_stock(self, index):
        data = self.combo_stock.itemData(index)
        if data:
            if data['peso_ini'] > 0:
                precio_kg = (data['precio_rollo'] / data['peso_ini']) * 1000
            else:
                precio_kg = 0
                
            self.spin_precio_kg.setValue(int(precio_kg))
            
            if data['peso_act'] < 100:
                self.lbl_info.setText(f"⚠️ QUEDA MUY POCO: {int(data['peso_act'])}g")
                self.lbl_info.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.lbl_info.setText(f"✅ Stock OK: {int(data['peso_act'])}g disponibles")
                self.lbl_info.setStyleSheet("color: #2ecc71")
        else:
            self.lbl_info.setText("Modo Manual: Precio personalizado")
            self.lbl_info.setStyleSheet("color: gray;")

    def calcular(self):
        try:
            cfg = self.backend.configuracion
            
            # Validar entrada
            if not self.input_peso.text():
                self.txt_res.setText("⚠️ Faltan datos: Ingresa el peso.")
                return 0, 0
            
            # --- 1. Obtener valores ---
            peso_pieza_base = float(self.input_peso.text().replace(',', '.') or 0)
            horas = self.spin_h.value() + (self.spin_m.value()/60)
            precio_mat_kg = self.spin_precio_kg.value()
            cant = self.spin_cant.value()
            
            margen_error = self.spin_margen.value() / 100
            hs_diseno = self.spin_hs_diseno.value() if self.chk_diseno.isChecked() else 0

            # --- 2. Cálculos Matemáticos ---
            
            # A. Material (incluyendo el fallo del 10%)
            peso_real_calculo = peso_pieza_base * (1 + margen_error) 
            costo_material = (peso_real_calculo / 1000) * precio_mat_kg
            
            # B. Máquina y Energía
            costo_luz = horas * cfg["consumo_kw"] * cfg["precio_kwh"]
            costo_maq = horas * cfg["precio_desgaste_hora"]
            
            # C. Suma de Costos Directos (Costo Puro)
            subtotal_costo_unitario = costo_material + costo_luz + costo_maq
            
            # D. Aplicar Ganancia
            ganancia_valor = subtotal_costo_unitario * (cfg["margen_ganancia"] / 100)
            precio_venta_unitario = subtotal_costo_unitario + ganancia_valor
            
            # E. Extras (Diseño se cobra una sola vez por lote)
            costo_diseno_total = hs_diseno * cfg["precio_hora_diseno"]
            
            # F. Totales Finales
            total_lote = (precio_venta_unitario * cant) + costo_diseno_total
            unitario_final_promedio = total_lote / cant

            # --- 3. Construir el Mensaje Detallado ---
            detalle = (
                f"📊 DETALLE UNITARIO (Base {peso_pieza_base}g + {int(margen_error*100)}% fallo):\n"
                f"   • Material: ${costo_material:,.2f}\n"
                f"   • Luz: ${costo_luz:,.2f} | Maq: ${costo_maq:,.2f}\n"
                f"   • Costo Puro: ${subtotal_costo_unitario:,.2f}\n"
                f"   • Ganancia ({cfg['margen_ganancia']}%): ${ganancia_valor:,.2f}\n"
                f"----------------------------------------\n"
                f"📦 LOTE x{cant} unid:\n"
                f"   • Piezas: ${precio_venta_unitario * cant:,.2f}\n"
                f"   • Diseño: ${costo_diseno_total:,.2f}\n"
                f"========================================\n"
                f"💰 TOTAL FINAL: ${total_lote:,.2f} (Unit: ${unitario_final_promedio:,.2f})"
            )
            
            self.txt_res.setText(detalle)
            
            return total_lote, unitario_final_promedio
            
        except Exception as e:
            self.txt_res.setText(f"❌ Error en cálculo: {e}")
            return 0, 0

    def guardar(self):
        total, unitario = self.calcular()
        
        if total > 0:
            if not self.input_cliente.text():
                QMessageBox.warning(self, "Atención", "Falta el nombre del cliente.")
                return

            # --- LÓGICA DE DESCUENTO DE STOCK ---
            data_stock = self.combo_stock.currentData()
            
            peso_pieza = float(self.input_peso.text().replace(',', '.') or 0)
            margen = self.spin_margen.value() / 100
            cant = self.spin_cant.value()
            consumo_total_gramos = (peso_pieza * cant) * (1 + margen)
            
            if data_stock:
                if data_stock['peso_act'] < consumo_total_gramos:
                    resp = QMessageBox.question(self, "Stock Insuficiente",
                        f"El lote requiere {int(consumo_total_gramos)}g pero solo quedan {int(data_stock['peso_act'])}g.\n"
                        "¿Deseas guardar igual y dejar el stock en negativo?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if resp == QMessageBox.StandardButton.No:
                        return 
                
                ok_stock = self.backend.descontar_stock(data_stock['id'], consumo_total_gramos)
                if not ok_stock:
                    QMessageBox.warning(self, "Alerta", "Se guardará el historial, pero falló el descuento de stock en Drive.")

            # --- GUARDADO EN HISTORIAL ---
            cli = self.input_cliente.text()
            mod = self.input_modelo.text() or "Pieza"
            fecha = datetime.now().strftime("%d/%m/%Y")
            mat_txt = self.combo_stock.currentText()
            hs_dis = self.spin_hs_diseno.value() if self.chk_diseno.isChecked() else 0
            
            fila = [
                fecha, "Usuario", cli, mod, "Impresión", mat_txt, "-",
                self.input_peso.text(), f"{self.spin_h.value()}h", 
                cant, f"{hs_dis} hs", f"${total:.2f}", f"${unitario:.2f}"
            ]
            
            ok = self.backend.guardar_fila_historial(fila)
            
            if ok:
                QMessageBox.information(self, "Hecho", "✅ Guardado y Stock Actualizado.")
                self.input_modelo.clear()
                self.txt_res.clear()
                self.actualizar_combo_stock()
            else:
                QMessageBox.critical(self, "Error", "Falló conexión Drive.")