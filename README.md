# 🚀 Stack de Monitoreo (Docker + Proxmox)

Este repositorio contiene una infraestructura completa de monitoreo, centralizada y orquestada mediante **Docker Compose**. El proyecto representa la migración de servicios individuales (LXC en Proxmox) a un entorno de **Infraestructura como Código (IaC)**, facilitando su despliegue en cualquier servidor en cuestión de segundos.

---

### 🛠️ Tecnologías y Herramientas

![Proxmox](https://img.shields.io/badge/Proxmox-E57000?style=for-the-badge&logo=proxmox&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=Prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/grafana-%23F46800.svg?style=for-the-badge&logo=grafana&logoColor=white)
![Uptime Kuma](https://img.shields.io/badge/Uptime%20Kuma-61DFA0?style=for-the-badge&logo=uptime-kuma&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

---

### 📋 Descripción del Sistema
El stack permite la supervisión integral de nodos Proxmox, contenedores, máquinas virtuales y dispositivos de red (routers/switches). Proporciona visualización de métricas, alertas en tiempo real y reportes de disponibilidad.

**Componentes del Stack:**
* **Prometheus:** Servidor central para la recolección y almacenamiento de métricas temporales.
* **Grafana:** Plataforma de análisis y visualización mediante Dashboards dinámicos.
* **Alertmanager:** Gestor de notificaciones y alertas basadas en reglas de Prometheus.
* **Blackbox Exporter:** Herramienta de monitoreo de disponibilidad mediante protocolos HTTP, HTTPS, ICMP (Ping) y DNS.
* **Uptime Kuma:** Interfaz moderna para el seguimiento visual del tiempo de actividad y respuesta de servicios.

---

### 📂 Estructura del Proyecto
La carpeta está organizada para que los archivos de configuración sean montados como volúmenes de solo lectura dentro de los contenedores:

```text
.
├── docker-compose.yml       # Orquestador maestro
├── prometheus/              # Configuración y reglas de Prometheus
├── alertmanager/            # Configuración de alertas
├── blackbox/                # Módulos de escaneo (ICMP, HTTP)
└── dashboards/              # Respaldos JSON de Grafana
