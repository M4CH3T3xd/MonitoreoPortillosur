# 🚀 Stack de Monitoreo — PortilloSur

Este repositorio contiene la infraestructura completa de monitoreo del sistema de PortilloSur, desplegada sobre **Proxmox VE** mediante contenedores **LXC**. El stack cubre tanto la **observabilidad de infraestructura** (servidores, red, sucursales) como la **observabilidad de negocio** (integración Toyota-Salesforce-SAP).

---

### 🛠️ Tecnologías y Herramientas

![Proxmox](https://img.shields.io/badge/Proxmox-E57000?style=for-the-badge&logo=proxmox&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=for-the-badge&logo=grafana&logoColor=white)
![Loki](https://img.shields.io/badge/Loki-F5A623?style=for-the-badge&logo=grafana&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

---

### 📋 Descripción del Sistema

El stack provee supervisión integral en dos niveles:

**Infraestructura:** Monitoreo de servidores Windows/Linux, conectividad ICMP hacia 10 sucursales y servidores críticos (Active Directory, SAP, Toyota, BMW), con alertas automáticas vía Telegram.

**Negocio:** Observabilidad del proceso de integración Toyota — desde la ingesta de oportunidades desde Salesforce hasta la facturación en SAP — mediante un exporter Python custom que expone métricas en tiempo real y logs estructurados JSON consultables desde Grafana.

---

### 🏗️ Arquitectura

```
Proxmox VE
├── CT 100 — Prometheus        (métricas, reglas, alertas)
├── CT 101 — Alertmanager      (notificaciones Telegram)
├── CT 102 — Blackbox Exporter (ping sucursales y servidores)
├── CT 103 — Grafana           (dashboards y visualización)
├── CT 104 — Uptime Kuma       (monitoreo de uptime)
└── CT 106 — Loki + Promtail + Toyota Exporter (logs y métricas de negocio)
```

---

### 📂 Estructura del Repositorio

```
.
├── prometheus/
│   ├── prometheus.yml          # Configuración principal y scrape jobs
│   └── rules/
│       ├── alert_rules.yml     # Alertas de infraestructura (CPU, RAM, disco, red)
│       ├── recording_rules.yml # Reglas híbridas Windows/Linux normalizadas
│       └── db_negocio_rules.yml # Alertas del proceso Toyota
├── alertmanager/
│   └── alertmanager.yml        # Routing de alertas → Telegram TI y Negocio
├── loki/
│   └── config.yml              # Configuración de Loki (retención 30d)
├── promtail/
│   └── config.yml              # Scraping de logs Toyota
├── exporters/
│   ├── shared/
│   │   └── db_utils.py         # Utilidades compartidas (logger JSON, conexión BD)
│   └── toyota/
│       └── toyota_exporter.py  # Exporter Python — métricas de negocio Toyota
└── grafana/
    └── dashboards/
        └── toyota_bd.json      # Dashboard Toyota Business Observability
```

---

### 📊 Métricas de Negocio — Toyota Exporter

El script `toyota_exporter.py` se conecta cada 60 segundos a PostgreSQL y monitorea el pipeline de ventas Toyota:

| Métrica | Descripción | Flujo |
|---|---|---|
| `toyota_lag_json` | Retraso en ingesta desde Salesforce | Flujo 1 |
| `toyota_sin_notaventa` | Oportunidades sin Nota de Venta (pendiente vendedor) | Flujo 2 |
| `toyota_atascados_sap` | Notas de Venta con error de cruce en SAP | Flujo 3 |
| `toyota_pendientes_totales` | Pipeline global sin facturar | Flujo 4 |
| `toyota_db_latencia_ms` | Latencia de respuesta PostgreSQL | Salud BD |

Los logs se escriben en formato JSON estructurado, son recolectados por Promtail y consultables desde Grafana vía LogQL.

---

### 🔔 Alertas configuradas

**Infraestructura (→ Telegram grupo TI):**
- Servidor inalcanzable por ping (2 min)
- Servidor sin métricas / exportador caído (5 min)
- CPU > 90% sostenido (5 min)
- RAM > 90% sostenida (5 min)
- Disco > 90% (10 min)
- Latencia de red > 150ms (3 min)
- Pérdida de paquetes > 10% (5 min)

**Negocio (→ Telegram grupo Negocio):**
- Servicio Toyota caído (1 min)
- Notas de Venta atascadas en SAP (5 min)
- Retraso en gestión comercial > 10 oportunidades (15 min)

---

### ⚙️ Variables de entorno

Los archivos `.env` no se incluyen en el repositorio por seguridad. Crear `/opt/exporters/toyota/toyota.env` con:

```
DB_NAME=GESTOR_PROYECTOS
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=ip_del_servidor
DB_PORT=5432
```

---

### 📝 Notas

- Los tokens de Telegram en `alertmanager.yml` han sido reemplazados por placeholders.
- Los servicios corren como unidades systemd en cada LXC.
- Prometheus tiene retención configurada a 30 días con límite de 5GB.