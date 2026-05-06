import sys
sys.path.insert(0, '/opt/exporters/shared')

import time
from db_utils import get_logger, ejecutar_select, ejecutar_select_all
from prometheus_client import start_http_server, Gauge

# ==========================================
# LOGGER — apunta a la nueva ruta de logs
# ==========================================
logger = get_logger("toyota_exporter", "/var/log/exporters/toyota/toyota.log")

# ==========================================
# MÉTRICAS PROMETHEUS
# ==========================================
PROMETHEUS_LATENCIA      = Gauge('toyota_db_latencia_ms',     'Salud BD: Tiempo de respuesta (ms)')
PROMETHEUS_PENDIENTES    = Gauge('toyota_pendientes_totales',  'Flujo 4: Oportunidades que faltan por facturar')
PROMETHEUS_ATASCADOS_SAP = Gauge('toyota_atascados_sap',       'Flujo 3: Errores al cruzar NV con SAP')
PROMETHEUS_SIN_NV        = Gauge('toyota_sin_notaventa',       'Flujo 2: Oportunidades esperando gestión del vendedor')
PROMETHEUS_LAG_JSON      = Gauge('toyota_lag_json',            'Flujo 1: Retraso en la ingesta de datos desde Salesforce')


# ==========================================
# LÓGICA DE MÉTRICAS
# ==========================================
def actualizar_metricas():

    # ---------------------------------------------------------
    # SALUD BÁSICA (Latencia)
    # ---------------------------------------------------------
    ok_salud, _, latencia = ejecutar_select(logger,
        "SELECT MAX(origen_fecha) FROM oportunidades_toyota.oportunidades_procesadas;"
    )
    if ok_salud:
        PROMETHEUS_LATENCIA.set(latencia)

    # ---------------------------------------------------------
    # FLUJO 1 — Lag Salesforce vs BD Local
    # ---------------------------------------------------------
    query_lag = """
        SELECT (SELECT COUNT(*) FROM oportunidades_toyota.opportunity_json)
             - (SELECT COUNT(*) FROM oportunidades_toyota.oportunidades_procesadas);
    """
    _, res_lag, _ = ejecutar_select(logger, query_lag)
    if res_lag:
        lag_val = max(0, res_lag[0])
        PROMETHEUS_LAG_JSON.set(lag_val)

        if lag_val > 0:
            q_det_lag = """
                SELECT id FROM oportunidades_toyota.opportunity_json
                WHERE id NOT IN (
                    SELECT origen_id FROM oportunidades_toyota.oportunidades_procesadas
                    WHERE origen_id IS NOT NULL
                ) LIMIT 5;
            """
            _, det_lag, _ = ejecutar_select_all(logger, q_det_lag)
            registros = [str(d[0]) for d in det_lag] if det_lag else []
            logger.warning(f"Desviación de Ingesta: {lag_val} registros pendientes", extra={
                "extra_data": {"action": "retraso_ingesta_salesforce", "registros_afectados": registros}
            })
        else:
            logger.info("Sincronización óptima: 0 registros pendientes de procesamiento", extra={
                "extra_data": {"action": "retraso_ingesta_salesforce", "status": "ok"}
            })

    # ---------------------------------------------------------
    # FLUJO 2 — Oportunidades sin Nota de Venta
    # ---------------------------------------------------------
    query_nv = """
        SELECT COUNT(p.id)
        FROM oportunidades_toyota.oportunidades_procesadas p
        LEFT JOIN public.oportunidades_toyota_notaventa nv ON p.quote_id = nv.quote_id
        WHERE nv.id IS NULL;
    """
    _, res_nv, _ = ejecutar_select(logger, query_nv)
    if res_nv:
        cant_nv = res_nv[0]
        PROMETHEUS_SIN_NV.set(cant_nv)

        if cant_nv > 0:
            q_det_nv = """
                SELECT p.quote_id, p.quote_seller_name
                FROM oportunidades_toyota.oportunidades_procesadas p
                LEFT JOIN public.oportunidades_toyota_notaventa nv ON p.quote_id = nv.quote_id
                WHERE nv.id IS NULL LIMIT 5;
            """
            _, det_nv, _ = ejecutar_select_all(logger, q_det_nv)
            registros = [f"Quote: {d[0]} | Asignado: {d[1]}" for d in det_nv] if det_nv else []
            logger.warning(f"Auditoría Operativa: {cant_nv} pendientes de gestión", extra={
                "extra_data": {"action": "auditoria_gestion_comercial", "registros_afectados": registros}
            })
        else:
            logger.info("Gestión Comercial al día: 0 pendientes", extra={
                "extra_data": {"action": "auditoria_gestion_comercial", "status": "ok"}
            })

    # ---------------------------------------------------------
    # FLUJO 3 — Notas de Venta atascadas en SAP
    # ---------------------------------------------------------
    query_sap = """
        SELECT COUNT(nv.id)
        FROM public.oportunidades_toyota_notaventa nv
        LEFT JOIN public.oportunidades_toyota_nv_fact fact
            ON nv.nro_nota_venta = fact.u_nodocdiller::varchar
        WHERE fact.docentry IS NULL;
    """
    _, res_sap, _ = ejecutar_select(logger, query_sap)
    if res_sap:
        cant_sap = res_sap[0]
        PROMETHEUS_ATASCADOS_SAP.set(cant_sap)

        if cant_sap > 0:
            q_det_sap = """
                SELECT nv.nro_nota_venta, nv.quote_id
                FROM public.oportunidades_toyota_notaventa nv
                LEFT JOIN public.oportunidades_toyota_nv_fact fact
                    ON nv.nro_nota_venta = fact.u_nodocdiller::varchar
                WHERE fact.docentry IS NULL LIMIT 5;
            """
            _, det_sap, _ = ejecutar_select_all(logger, q_det_sap)
            registros = [f"NV: {d[0]} | Quote: {d[1]}" for d in det_sap] if det_sap else []
            logger.error(f"Excepción de Integración: {cant_sap} fallas detectadas", extra={
                "extra_data": {"action": "error_integracion_sap", "registros_afectados": registros}
            })
        else:
            logger.info("Integración SAP estable: 0 errores", extra={
                "extra_data": {"action": "error_integracion_sap", "status": "ok"}
            })

    # ---------------------------------------------------------
    # FLUJO 4 — Pipeline de Ventas global
    # ---------------------------------------------------------
    query_pend = """
        SELECT COUNT(id) FROM oportunidades_toyota.oportunidades_procesadas
        WHERE opp_stage_name != 'FACTURADA' OR opp_stage_name IS NULL;
    """
    _, res_pend, _ = ejecutar_select(logger, query_pend)
    if res_pend:
        cant_pend = res_pend[0]
        PROMETHEUS_PENDIENTES.set(cant_pend)

        q_det_pend = """
            SELECT opp_stage_name, COUNT(id)
            FROM oportunidades_toyota.oportunidades_procesadas
            WHERE opp_stage_name != 'FACTURADA' OR opp_stage_name IS NULL
            GROUP BY opp_stage_name;
        """
        _, det_pend, _ = ejecutar_select_all(logger, q_det_pend)
        desglose = {str(d[0] if d[0] else 'Sin Etapa'): d[1] for d in det_pend} if det_pend else {}

        logger.info(f"Estado del Pipeline: {cant_pend} unidades", extra={
            "extra_data": {"action": "volumen_pipeline_ventas", "detalle_operativo": desglose}
        })


# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    puerto = 8000
    start_http_server(puerto)
    logger.info("Toyota Exporter iniciado", extra={"extra_data": {"puerto": puerto, "ciclo_segundos": 60}})

    while True:
        actualizar_metricas()
        logger.info("Metricas actualizadas y enviadas", extra={"extra_data": {"action": "update_metrics"}})
        time.sleep(60)
