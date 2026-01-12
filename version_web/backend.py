import os
import json
import time  # <--- NUEVO: Para generar IDs únicos
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class BackendGestor:
    def __init__(self):
        # Nombres de archivos y hojas
        self.CONFIG_FILE = "configuracion.json"
        self.CREDENTIALS_JSON = 'credenciales.json'
        self.SHEET_NAME = 'PythonProyecTabla'
        
        # Datos en memoria (Variables globales para la app)
        self.configuracion = {}
        self.inventario = []
        
        # Valores por defecto por si falla la carga
        self.default_config = {
            "precio_kwh": 170, 
            "consumo_kw": 0.2, 
            "precio_hora_diseno": 8500,
            "margen_ganancia": 100, 
            "precio_desgaste_hora": 200
        }
        
        self.sheet_historial = None
        self.sheet_inventario = None
        
        # Cargar datos al iniciar
        self.load_local_config()
        self.conectar_drive()

    def load_local_config(self):
        """Carga la configuración desde el archivo JSON local"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.configuracion = data.get("configuracion", self.default_config)
            except:
                self.configuracion = self.default_config
        else:
            self.configuracion = self.default_config

    def save_local_config(self):
        """Guarda la configuración actual en el JSON"""
        try:
            with open(self.CONFIG_FILE, "w") as f:
                json.dump({"configuracion": self.configuracion}, f, indent=4)
            return True
        except:
            return False

    def conectar_drive(self):
        """Conecta a Google Sheets y descarga el inventario"""
        if not os.path.exists(self.CREDENTIALS_JSON):
            print("⚠️ No se encontró credenciales.json")
            return False
        
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_JSON, scope)
            client = gspread.authorize(creds)
            
            # Abrir hoja de cálculo
            doc = client.open(self.SHEET_NAME)
            
            # Hoja 1: Historial
            self.sheet_historial = doc.sheet1
            
            # Hoja 2: Inventario
            try:
                self.sheet_inventario = doc.get_worksheet(1)
                # Descargar inventario a memoria
                self.inventario = self.sheet_inventario.get_all_records()
            except:
                print("⚠️ No se encontró la hoja 2 (Inventario)")
                self.inventario = []
                
            return True
        except Exception as e:
            print(f"❌ Error conectando a Drive: {e}")
            return False

    def guardar_fila_historial(self, datos):
        """Sube una fila al historial (Hoja 1)"""
        if self.sheet_historial:
            try:
                self.sheet_historial.append_row(datos)
                return True
            except:
                return False
        return False

    def agregar_stock_nube(self, datos_fila):
        """
        Sube un nuevo rollo al inventario (Hoja 2).
        Genera un ID único y lo inserta al principio.
        """
        if self.sheet_inventario:
            try:
                # Generamos ID único basado en el tiempo
                id_unico = int(time.time())
                
                # Insertamos el ID en la posición 0 de la lista
                datos_fila.insert(0, id_unico)
                
                self.sheet_inventario.append_row(datos_fila)
                
                # Actualizamos memoria local inmediatamente
                self.forzar_descarga_inventario()
                return True
            except:
                return False
        return False
        
    def obtener_historial_completo(self):
        """Descarga todos los datos de la hoja Historial"""
        if self.sheet_historial:
            try:
                datos = self.sheet_historial.get_all_values()
                return datos
            except Exception as e:
                print(f"Error leyendo historial: {e}")
                return []
        return []

    def forzar_descarga_inventario(self):
        """Borra la memoria local y baja todo fresco de Google Sheets"""
        if self.sheet_inventario:
            try:
                nuevos_datos = self.sheet_inventario.get_all_records()
                if nuevos_datos:
                    self.inventario = nuevos_datos
                    print(f"✅ Inventario actualizado: {len(self.inventario)} items.")
                    return True
                else:
                    self.inventario = [] 
                    return True
            except Exception as e:
                print(f"❌ Error descargando inventario: {e}")
                return False
        return False

    def descontar_stock(self, id_rollo, gramos_consumidos):
        """
        Busca el rollo por ID y resta los gramos a la columna 'Peso_Actual'.
        """
        if not self.sheet_inventario: return False
        
        try:
            # 1. Buscar en qué fila está ese ID
            # Nota: find devuelve la celda si la encuentra
            celda_id = self.sheet_inventario.find(str(id_rollo))
            
            if celda_id:
                fila = celda_id.row
                # La columna de Peso_Actual es la 8 (H) en el nuevo formato:
                # ID(1)|Fecha(2)|Marca(3)|Tipo(4)|Color(5)|Acabado(6)|Peso_In(7)|Peso_Act(8)|Precio(9)
                col_peso_actual = 8 
                
                # Obtener valor actual
                valor_actual_raw = self.sheet_inventario.cell(fila, col_peso_actual).value
                valor_actual = float(valor_actual_raw) if valor_actual_raw else 0
                
                nuevo_peso = valor_actual - float(gramos_consumidos)
                
                # Actualizar en la nube
                self.sheet_inventario.update_cell(fila, col_peso_actual, int(nuevo_peso))
                
                # Actualizar memoria local
                self.forzar_descarga_inventario()
                return True
            else:
                print(f"❌ No se encontró el ID {id_rollo} en Drive")
                return False
        except Exception as e:
            print(f"❌ Error descontando stock: {e}")
            return False

    def obtener_historial_completo(self):
        """Descarga todas las filas de la hoja Historial"""
        if self.sheet_historial:
            try:
                # get_all_values devuelve una lista de listas
                return self.sheet_historial.get_all_values()
            except Exception as e:
                print(f"Error descargando historial: {e}")
                return []
        return []

    def borrar_fila_historial(self, indice_lista):
        """
        Borra una fila basada en el índice de la lista visual.
        NOTA: En Google Sheets, la fila 1 es el encabezado.
        La fila 0 de tu lista visual corresponde a la fila 2 de Sheets.
        """
        if self.sheet_historial:
            try:
                # Sumamos 2: +1 por ser base-1 (Sheets) y +1 por el encabezado
                fila_a_borrar = indice_lista + 2 
                self.sheet_historial.delete_rows(fila_a_borrar)
                return True
            except Exception as e:
                print(f"Error borrando fila: {e}")
                return False
        return False        