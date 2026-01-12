# 🚀 Snok App - Sistema de Gestión de Impresión 3D

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Web_App-ff4b4b)
![Google Sheets](https://img.shields.io/badge/Database-Google_Sheets-green)

Aplicación integral para la administración de un taller de impresión 3D. Permite cotizar piezas con precisión, gestionar el inventario de filamentos en tiempo real y llevar un registro histórico de ventas sincronizado en la nube.

## ✨ Características Principales

* **🖨️ Cotizador Inteligente:** Calcula el precio final basándose en peso, tiempo de impresión, coste eléctrico, desgaste de máquina y horas de diseño.
* **📦 Gestión de Stock:** Base de datos de rollos de filamento. Descuenta automáticamente el material consumido al guardar una impresión.
* **☁️ Base de Datos en la Nube:** Conexión directa con Google Sheets (Google Drive) para mantener los datos seguros y accesibles desde cualquier lugar.
* **📋 Historial de Ventas:** Registro detallado de cada trabajo realizado.
* **📱 Interfaz Web (Streamlit):** Diseño responsivo apto para usar desde PC o Celular.

## 🛠️ Tecnologías

* **Lenguaje:** Python
* **Interfaz Web:** Streamlit
* **Backend/Lógica:** Python nativo (`backend.py`)
* **Base de Datos:** Google Sheets API (`gspread`)

## 🚀 Instalación y Uso Local

Sigue estos pasos para ejecutar la aplicación en tu computadora:

### 1. Clonar el repositorio
```bash
git clone [https://github.com/Nahuel023/snok_app.git](https://github.com/Nahuel023/snok_app.git)
cd snok_app
