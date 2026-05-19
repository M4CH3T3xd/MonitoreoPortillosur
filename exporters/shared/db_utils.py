import time
import psycopg2
import logging
import json
import os
from datetime import datetime, timezone

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

def init_tracer(service_name="toyota_exporter"):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint="http://10.56.6.16:4318/v1/traces"
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

tracer = init_tracer()

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
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(log_path)
    handler.setFormatter(JSONFormatter(app_name))
    logger.addHandler(handler)
    return logger

def get_db_config():
    return {
        "dbname":          os.environ.get("DB_NAME"),
        "user":            os.environ.get("DB_USER"),
        "password":        os.environ.get("DB_PASSWORD"),
        "host":            os.environ.get("DB_HOST"),
        "port":            os.environ.get("DB_PORT", "5432"),
        "connect_timeout": 5,
        "options":         "-c statement_timeout=5000"
    }

def ejecutar_select(logger, query, span_name="query"):
    start_time = time.time()
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.statement", query.strip()[:200])
        span.set_attribute("db.host", os.environ.get("DB_HOST", "unknown"))
        span.set_attribute("db.name", os.environ.get("DB_NAME", "unknown"))
        try:
            conn = psycopg2.connect(**get_db_config(), client_encoding='utf8')
            cursor = conn.cursor()
            cursor.execute(query)
            resultado = cursor.fetchone()
            cursor.close()
            conn.close()
            latencia = (time.time() - start_time) * 1000
            span.set_attribute("db.latencia_ms", round(latencia, 2))
            span.set_attribute("db.resultado", "ok")
            return True, resultado, latencia
        except Exception as e:
            span.set_attribute("db.resultado", "error")
            span.set_attribute("db.error", str(e)[:150])
            span.record_exception(e)
            logger.error("Error de conexion a Base de Datos", extra={"extra_data": {
                "action": "ejecutar_select",
                "error_det": str(e)[:150]
            }})
            return False, None, 0

def ejecutar_select_all(logger, query, span_name="query_all"):
    start_time = time.time()
    with tracer.start_as_current_span(span_name) as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.statement", query.strip()[:200])
        span.set_attribute("db.host", os.environ.get("DB_HOST", "unknown"))
        span.set_attribute("db.name", os.environ.get("DB_NAME", "unknown"))
        try:
            conn = psycopg2.connect(**get_db_config(), client_encoding='utf8')
            cursor = conn.cursor()
            cursor.execute(query)
            resultado = cursor.fetchall()
            cursor.close()
            conn.close()
            latencia = (time.time() - start_time) * 1000
            span.set_attribute("db.latencia_ms", round(latencia, 2))
            span.set_attribute("db.resultado", "ok")
            span.set_attribute("db.filas", len(resultado) if resultado else 0)
            return True, resultado, latencia
        except Exception as e:
            span.set_attribute("db.resultado", "error")
            span.set_attribute("db.error", str(e)[:150])
            span.record_exception(e)
            logger.error("Error BD Listas", extra={"extra_data": {
                "action": "ejecutar_select_all",
                "error_det": str(e)[:150]
            }})
            return False, None, 0
