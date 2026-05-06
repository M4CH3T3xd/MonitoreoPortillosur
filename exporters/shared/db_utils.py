import time
import psycopg2
import logging
import json
import os
from datetime import datetime, timezone


# ==========================================
# LOGGER JSON ESTRUCTURADO (compartido)
# ==========================================
class JSONFormatter(logging.Formatter):
    def __init__(self, app_name):
        super().__init__()
        self.app_name = app_name

    def format(self, record):
        log_record = {
            "time": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + "Z",
            "level": record.levelname,
            "app": self.app_name,
            "msg": record.getMessage()
        }
        if hasattr(record, 'extra_data'):
            log_record.update(record.extra_data)
        return json.dumps(log_record)


def get_logger(app_name, log_path):
    """
    Crea y retorna un logger JSON estructurado.
    Uso: logger = get_logger("toyota_exporter", "/var/log/exporters/toyota/toyota.log")
    """
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path)
    handler.setFormatter(JSONFormatter(app_name))
    logger.addHandler(handler)
    return logger


# ==========================================
# CONFIGURACIÓN DB DESDE VARIABLES DE ENTORNO
# ==========================================
def get_db_config():
    """
    Lee la configuración de BD desde variables de entorno.
    Estas variables se definen en el archivo .env de cada exporter.
    """
    return {
        "dbname":          os.environ.get("DB_NAME"),
        "user":            os.environ.get("DB_USER"),
        "password":        os.environ.get("DB_PASSWORD"),
        "host":            os.environ.get("DB_HOST"),
        "port":            os.environ.get("DB_PORT", "5432"),
        "connect_timeout": 5,
        "options":         "-c statement_timeout=5000"
    }


# ==========================================
# FUNCIONES DE CONSULTA
# ==========================================
def ejecutar_select(logger, query):
    """
    Ejecuta una query y retorna la primera fila.
    Retorna: (ok: bool, resultado: tuple|None, latencia_ms: float)
    """
    start_time = time.time()
    try:
        conn = psycopg2.connect(**get_db_config(), client_encoding='utf8')
        cursor = conn.cursor()
        cursor.execute(query)
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        return True, resultado, (time.time() - start_time) * 1000
    except Exception as e:
        logger.error("Error de conexion a Base de Datos", extra={"extra_data": {
            "action": "ejecutar_select",
            "error_det": str(e)[:150]
        }})
        return False, None, 0


def ejecutar_select_all(logger, query):
    """
    Ejecuta una query y retorna todas las filas.
    Retorna: (ok: bool, resultado: list|None, latencia_ms: float)
    """
    start_time = time.time()
    try:
        conn = psycopg2.connect(**get_db_config(), client_encoding='utf8')
        cursor = conn.cursor()
        cursor.execute(query)
        resultado = cursor.fetchall()
        cursor.close()
        conn.close()
        return True, resultado, (time.time() - start_time) * 1000
    except Exception as e:
        logger.error("Error BD Listas", extra={"extra_data": {
            "action": "ejecutar_select_all",
            "error_det": str(e)[:150]
        }})
        return False, None, 0
