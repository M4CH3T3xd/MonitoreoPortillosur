# 🚀 Stack de Monitoreo — PortilloSur

Este repositorio contiene la infraestructura completa de observabilidad de PortilloSur, desplegada sobre **Proxmox VE** mediante contenedores **LXC**. El stack cubre tanto la **observabilidad de infraestructura** (servidores, red, sucursales) como la **observabilidad de negocio** (integración Toyota-Salesforce-SAP) con trazas distribuidas y logs centralizados.

---

### 🛠️ Tecnologías y Herramientas

[![Proxmox](https://img.shields.io/badge/Proxmox-E57000?style=for-the-badge&logo=proxmox&logoColor=white)](https://www.proxmox.com)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)](https://prometheus.io)
[![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com)
[![Loki](https://img.shields.io/badge/Loki-F5A623?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/oss/loki)
[![Tempo](https://img.shields.io/badge/Tempo-F5A623?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/oss/tempo)
[![Mimir](https://img.shields.io/badge/Mimir-F5A623?style=for-the-badge&logo=grafana&logoColor=white)](https://grafana.com/oss/mimir)
[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://www.linux.org)
[![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://github.com)

---

### 📋 Descripción del Sistema

El stack provee supervisión integral en dos niveles:

**Infraestructura:** Monitoreo de servidores Windows/Linux, conectividad ICMP hacia 10 sucursales y servidores críticos (Active Directory, SAP, Toyota, BMW), con alertas automáticas vía Telegram separadas por tipo (sucursal vs servidor) y severidad.

**Negocio:** Observabilidad del proceso de integración Toyota — desde la ingesta de oportunidades desde Salesforce hasta la facturación en SAP — mediante un exporter Python custom instrumentado con OpenTelemetry que expone métricas Prometheus, logs JSON estructurados en Loki y trazas distribuidas en Tempo.

---

### 🏗️ Arquitectura — Stack LGTM

```
Proxmox VE (10.56.6.100)
├── CT 100 — Prometheus        (10.56.6.43:9090)   métricas, reglas, alertas
├── CT 101 — Alertmanager      (10.56.6.112:9093)  notificaciones Telegram
├── CT 102 — Blackbox Exporter (10.56.6.113:9115)  ping sucursales y servidores
├── CT 103 — Grafana           (10.56.6.94:3000)   dashboards y visualización
├── CT 105 — Tempo             (10.56.6.16:3200)   trazas distribuidas (OTLP)
├── CT 106 — Loki + Promtail + Toyota Exporter (10.56.6.49:3100)
└── CT 107 — Mimir             (10.56.6.18:9009)   retención long-term 90d

Servidores externos (10.10.70.x)
├── Active Directory  (10.10.70.36:9182)  Windows Exporter
├── Repo. BMW         (10.10.70.7:9182)   Windows Exporter
├── Server Dev Ubuntu (10.10.70.112:9100) Node Exporter
└── BD PostgreSQL     (10.10.70.69:5432)  Toyota Exporter
```

---

### 📂 Estructura del Repositorio

```
.
├── prometheus/
│   ├── prometheus.yml           # Configuración principal y scrape jobs
│   └── rules/
│       ├── alert_rules.yml      # Alertas sucursales, servidores e infraestructura
│       ├── recording_rules.yml  # Reglas híbridas Windows/Linux normalizadas
│       └── db_negocio_rules.yml # Alertas del proceso Toyota
├── alertmanager/
│   └── alertmanager.yml         # Routing alertas → Telegram TI y Negocio
├── loki/
│   └── config.yml               # Configuración Loki (retención 30d, schema v13)
├── promtail/
│   └── config.yml               # Scraping de logs Toyota Exporter
├── tempo/
│   └── config.yml               # Trazas OTLP, metrics_generator → Prometheus
├── mimir/
│   └── config.yml               # Almacenamiento long-term (retención 90d)
├── exporters/
│   ├── shared/
│   │   └── db_utils.py          # Logger JSON, conexión BD, spans OpenTelemetry
│   └── toyota/
│       └── toyota_exporter.py   # Exporter Python — métricas y trazas Toyota
└── grafana/
    └── dashboards/
        ├── estado_general_portillosur.json   # Dashboard principal con Toyota + Tempo
        ├── metricas_servidores.json          # Métricas detalladas por servidor
        └── conectividad_sucursales.json      # Conectividad y uptime sucursales
```

---

### 📊 Métricas de Negocio — Toyota Exporter

El script `toyota_exporter.py` se conecta cada 60 segundos a PostgreSQL e instrumenta cada query como un span OpenTelemetry hacia Tempo:

| Métrica | Descripción | Flujo |
|---|---|---|
| `toyota_lag_json` | Retraso en ingesta desde Salesforce | Flujo 1 |
| `toyota_sin_notaventa` | Oportunidades sin Nota de Venta | Flujo 2 |
| `toyota_atascados_sap` | Notas de Venta con error en SAP | Flujo 3 |
| `toyota_pendientes_totales` | Pipeline global sin facturar | Flujo 4 |
| `toyota_db_latencia_ms` | Latencia de respuesta PostgreSQL | Salud BD |

Los logs se escriben en formato JSON estructurado, recolectados por Promtail y consultables desde Grafana vía LogQL. Las trazas se envían a Tempo vía OTLP HTTP y sus métricas (`traces_spanmetrics_*`) se envían a Prometheus para graficar latencia por flujo.

---

### 🔔 Alertas Configuradas

**Sucursales (→ Telegram grupo TI):**
- Sucursal inalcanzable por ping (2 min) — severity: fatal
- Latencia > 150ms sostenida (3 min) — severity: warning
- Pérdida de paquetes > 10% (5 min) — severity: critical

**Servidores (→ Telegram grupo TI):**
- Servidor inalcanzable por ping (2 min) — severity: fatal
- Exportador caído / sin métricas (5 min) — severity: warning
- Latencia > 150ms sostenida (3 min) — severity: warning

**Infraestructura (→ Telegram grupo TI):**
- CPU > 90% sostenido (5 min) — severity: critical
- RAM > 90% sostenida (5 min) — severity: critical
- Disco > 90% (10 min) — severity: critical
- Cola CPU > 10 procesos (5 min) — severity: warning

**Negocio (→ Telegram grupo Negocio):**
- Servicio Toyota caído
- Notas de Venta atascadas en SAP
- Retraso en gestión comercial

---

### 📊 Dashboards Grafana

| UID | Título | Descripción |
|---|---|---|
| `estado_general_portillosur` | 🏢 Estado General | Vista unificada infraestructura + Toyota + Trazas Tempo |
| `adbttrj` | 🖥️ Métricas Servidores | CPU, RAM, disco, red por servidor |
| `adf5jnh` | 🌐 Conectividad Sucursales | Ping, latencia, uptime por sucursal |

---

### 🔭 Observabilidad — Stack LGTM

| Pilar | Herramienta | Qué monitorea |
|---|---|---|
| Métricas | Prometheus + Mimir | Infraestructura, negocio, spans |
| Logs | Loki + Promtail | Toyota Exporter, syslogs de CTs |
| Trazas | Tempo + OpenTelemetry | Queries SQL por flujo Toyota |
| Visualización | Grafana | Dashboards unificados |

---

### ⚙️ Variables de Entorno

Los archivos `.env` no se incluyen en el repositorio por seguridad. Crear `/opt/exporters/toyota/toyota.env` con:

```env
DB_NAME=GESTOR_PROYECTOS
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=10.10.70.69
DB_PORT=5432
```

---

### 📝 Notas

- Los tokens de Telegram en `alertmanager.yml` han sido reemplazados por placeholders.
- Los servicios corren como unidades systemd en cada LXC.
- Prometheus retención: 30 días / 5GB. Mimir retención: 90 días.
- Promtail instalado en CTs 100, 101, 102, 103, 105, 106, 107.
- WireGuard configurado en Proxmox host (10.200.0.1) — Server Dev Ubuntu pendiente acceso físico.