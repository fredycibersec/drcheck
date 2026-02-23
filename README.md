# 🔍 Dr.Check (Domain Reputation Checker) - OSINT Tool

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

<p align="center">
  <img width="500" alt="image" src="https://github.com/user-attachments/assets/ce5527fc-398a-44a9-98f1-558ae0772c0c" />
</p>

**Domain Reputation Checker** es una herramienta profesional de OSINT (Open Source Intelligence) para analizar la reputación de dominios, direcciones IP y hashes de archivos utilizando múltiples fuentes de inteligencia de amenazas.

<img width="950" alt="image" src="https://github.com/user-attachments/assets/60b34b03-76f9-43c4-965d-36925da10c67" />



## ✨ Características Principales

### 🌐 Análisis de Dominios
- ✅ Verificación de reputación mediante múltiples fuentes de threat intelligence
- ✅ **Sin consultas DNS directas** - evita alertar a los objetivos investigados
- ✅ Detección de dominios recién registrados (suspicious)
- ✅ Análisis de categorización y reputación histórica
- ✅ Integración con VirusTotal, URLVoid, AlienVault OTX, y más

### 🌍 Análisis de IPs
- ✅ Verificación contra 20+ listas negras en tiempo real
- ✅ Análisis de reputación de ASN (Autonomous System Number)
- ✅ Inteligencia de amenazas por país y región
- ✅ Geolocalización y detección de hosting provider
- ✅ Detección de proxies, VPN y servicios de anonimización
- ✅ Clasificación automática: Maliciosa, Sospechosa o Limpia

### 🔐 Análisis de Hashes
- ✅ Búsqueda en MalwareBazaar (base de datos de malware)
- ✅ Verificación con VirusTotal
- ✅ Soporte para MD5, SHA1 y SHA256
- ✅ Información sobre familias de malware conocidas
- ✅ Metadatos e indicadores de compromiso (IoC)

### 📊 Sistema de Scoring Inteligente
- ✅ **Sistema de pesos por Tiers** - prioriza fuentes más confiables
- ✅ **Reduce falsos positivos en un 40%** vs promedios simples
- ✅ 4 niveles de confiabilidad (Tier 1-4) con pesos diferenciados
- ✅ Override automático para detecciones críticas
- ✅ Documentación transparente del sistema de scoring

### 🎨 Interfaz Moderna
- ✅ Dashboard responsivo con tema oscuro/claro
- ✅ Mapa interactivo de amenazas por país
- ✅ Gráficos de estadísticas en tiempo real
- ✅ Historial completo de búsquedas con filtros
- ✅ Panel de configuración de APIs con verificación

## 🚀 Instalación Rápida

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git (opcional)

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/Domain-Reputation-WebApp.git
cd Domain-Reputation-WebApp
```

### 2. Crear Entorno Virtual
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar API Keys
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar con tus API keys
nano .env  # o usa tu editor preferido
chmod 600 .env  # Proteger el archivo
```

### 5. Ejecutar la Aplicación
```bash
python app.py
```

Abre tu navegador en `http://localhost:5000` 🎉

## 🔑 Configuración de API Keys

### APIs Recomendadas (Tier 1 - Máxima Prioridad)

#### **VirusTotal** (⭐ Esencial)
- **Qué hace:** Analiza con 70+ motores antivirus
- **Obtener:** [https://www.virustotal.com/gui/my-apikey](https://www.virustotal.com/gui/my-apikey)
- **Precio:** Gratis (4 req/min) o Premium
- **Variable:** `VIRUSTOTAL_API_KEY`

#### **AbuseIPDB** (⭐ Muy recomendada)
- **Qué hace:** Reportes validados de IPs maliciosas
- **Obtener:** [https://www.abuseipdb.com/account/api](https://www.abuseipdb.com/account/api)
- **Precio:** Gratis (1000 consultas/día)
- **Variable:** `ABUSEIPDB_API_KEY`

#### **AlienVault OTX** (⭐ Recomendada)
- **Qué hace:** Threat intelligence profesional
- **Obtener:** [https://otx.alienvault.com/api](https://otx.alienvault.com/api)
- **Precio:** Gratis
- **Variable:** `ALIENVAULT_API_KEY`

### APIs Tier 2 (Alta Confiabilidad)

- **URLScan.io:** [https://urlscan.io/user/signup](https://urlscan.io/user/signup) - `URLSCAN_API_KEY`
- **ThreatFox:** [https://threatfox.abuse.ch/api/](https://threatfox.abuse.ch/api/) - `THREATFOX_API_KEY`
- **Abuse.ch:** [https://bazaar.abuse.ch/api/](https://bazaar.abuse.ch/api/) - `ABUSECH_API_KEY`

### APIs Tier 3 (Contextuales)

- **APIVoid (URLVoid):** [https://www.apivoid.com/](https://www.apivoid.com/) - `APIVOID_KEY`
- **Shodan:** [https://account.shodan.io/](https://account.shodan.io/) - `SHODAN_API_KEY`
- **SecurityTrails:** [https://securitytrails.com/](https://securitytrails.com/) - `SECURITYTRAILS_API_KEY`

### APIs Tier 4 (Complementarias)

- **IP-API:** [https://ipapi.com/](https://ipapi.com/) - `IPAPI_ACCESS_KEY` (versión gratuita disponible)
- **IPData:** [https://ipdata.co/](https://ipdata.co/) - `IPDATA_API_KEY`

> 📝 **Nota:** Con solo VirusTotal y AbuseIPDB ya tienes un análisis muy robusto. Las demás APIs mejoran la precisión y reducen falsos positivos.

## 🛠️ Instalación como Servicio (Linux)

Para ejecutar la aplicación como un servicio systemd que inicia automáticamente:

### 1. Usar el Script de Instalación
```bash
sudo ./scripts/install-service.sh
```

### 2. Gestión del Servicio
```bash
# Ver estado
sudo systemctl status domain-reputation-webapp

# Reiniciar
sudo systemctl restart domain-reputation-webapp

# Ver logs
sudo journalctl -u domain-reputation-webapp -f

# Detener
sudo systemctl stop domain-reputation-webapp
```

El servicio carga las API keys de forma segura desde un archivo de entorno con permisos restringidos (600).

## 📖 Uso

### Análisis de Dominios
1. Ir a la sección **"Analizar Dominio"**
2. Ingresar el dominio (ej: `example.com`)
3. Click en **"Buscar"**
4. Ver resultados detallados con:
   - Score de reputación general
   - Detecciones por fuente
   - Información WHOIS
   - Categorización
   - Mapa de amenazas

### Análisis de IPs
1. Ir a la sección **"Analizar IP"**
2. Ingresar la dirección IP (ej: `8.8.8.8`)
3. Ver resultados con:
   - Clasificación (Limpia/Sospechosa/Maliciosa)
   - Geolocalización
   - ASN y proveedor
   - Listas negras detectadas
   - Puertos abiertos (si disponible)

### Análisis de Hashes
1. Ir a la sección **"Analizar Hash"**
2. Ingresar el hash (MD5, SHA1 o SHA256)
3. Ver resultados con:
   - Detecciones de malware
   - Familia de malware
   - Metadatos del archivo
   - IoCs relacionados

### Panel de Configuración
1. Click en **"Configuración"** en la barra lateral
2. Ingresar tus API keys por tier
3. Click en **"Verificar APIs"** para confirmar que funcionan
4. **Guardar Configuración** (se almacena cifrada)

## 📊 Sistema de Scoring

El sistema utiliza un **scoring ponderado por tiers** que prioriza fuentes más confiables:

| Tier | Peso | Fuentes | Precisión |
|------|------|---------|-----------|
| 🏆 Tier 1 | 3.0 | VirusTotal, AbuseIPDB, AlienVault OTX | 90-95% |
| ⭐ Tier 2 | 2.0 | URLScan, ThreatFox, MalwareBazaar | 88-98% |
| ⚡ Tier 3 | 1.5 | Shodan, URLVoid, SecurityTrails | 70-75% |
| 🔧 Tier 4 | 1.0 | WHOIS, Geolocation, Otros | 60-65% |

**Fórmula:** `Score = Σ(Reputación × Peso) / ΣPesos`

**Valores de Reputación:**
- Clean: +1
- Questionable: -1
- Suspicious: -2
- Malicious: -3

**Umbrales de Clasificación:**
- ≥ 0.3 → **Clean** ✅
- ≥ -0.7 → **Questionable** ⚠️
- ≥ -1.5 → **Suspicious** 🟠
- < -1.5 → **Malicious** 🔴

### Ventajas del Sistema
✅ **40% menos falsos positivos** vs promedio simple  
✅ Prioriza detecciones de fuentes Tier 1 y 2  
✅ Override automático en detecciones críticas (VT ≥10, AbuseIPDB ≥90%)  
✅ Transparente y documentado en `docs/SOURCE_RELIABILITY_RANKING.md`

## 🎨 Temas

La aplicación soporta **tema oscuro y claro** con cambio automático:
- Navegación/sidebar oscura con contenido claro (modo light)
- Colores pastel profesionales
- Alta legibilidad y contraste
- Persistencia de preferencia en localStorage

## 📁 Estructura del Proyecto

```
Domain-Reputation-WebApp/
├── app.py                      # Aplicación Flask principal
├── api_manager.py              # Gestión de API keys cifradas
├── wsgi.py                     # Entry point para WSGI
├── requirements.txt            # Dependencias Python
├── .env.example                # Plantilla de configuración
├── .gitignore                  # Archivos ignorados por Git
├── README.md                   # Este archivo
├── static/                     # Archivos estáticos
│   ├── dashboard-script.js     # Lógica del frontend
│   ├── dashboard-styles.css    # Estilos CSS
│   ├── favicon.svg             # Favicon
│   └── logo.svg                # Logo de la aplicación
├── templates/                  # Plantillas HTML
│   └── index.html              # Interfaz principal
├── docs/                       # Documentación
│   ├── SOURCE_RELIABILITY_RANKING.md
│   └── API_INTEGRATION.md
└── scripts/                    # Scripts de utilidad
    ├── install-service.sh      # Instalador de servicio systemd
    └── setup.sh                # Setup automático
```

## 🔒 Seguridad

### Buenas Prácticas Implementadas
✅ API keys cifradas con Fernet (cryptography)  
✅ Variables de entorno con permisos 600  
✅ No se almacenan secretos en Git (.gitignore configurado)  
✅ Sin consultas DNS directas (modo stealth)  
✅ Sanitización de inputs  
✅ Rate limiting en consultas API  

### Recomendaciones
- **NUNCA** compartas tu archivo `.env` o `flask-app.env`
- Usa `chmod 600` en archivos de configuración
- Regenera API keys si las expones accidentalmente
- Mantén las dependencias actualizadas: `pip install -U -r requirements.txt`

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

**SaruMan**  
Herramienta desarrollada para investigaciones OSINT y análisis de seguridad.

## 🙏 Agradecimientos

- VirusTotal por su API pública
- Abuse.ch por MalwareBazaar y ThreatFox
- AbuseIPDB por la detección de IPs maliciosas
- La comunidad OSINT por las mejores prácticas
- Chart.js por las visualizaciones

## 📚 Recursos Adicionales

- [Documentación del Sistema de Scoring](docs/SOURCE_RELIABILITY_RANKING.md)
- [Guía de Integración de APIs](docs/API_INTEGRATION.md)
- [VirusTotal API Docs](https://developers.virustotal.com/reference/overview)
- [AbuseIPDB API Docs](https://docs.abuseipdb.com/)

## ⚠️ Disclaimer

Esta herramienta está diseñada para investigaciones OSINT legítimas y análisis de seguridad. El autor no se hace responsable del uso indebido o ilegal de esta herramienta. Úsala de manera ética y respetando las leyes aplicables.

---

⭐ Si te ha sido útil, considera dejar una estrella en GitHub!
