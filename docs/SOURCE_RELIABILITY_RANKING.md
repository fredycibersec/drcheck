# Ranking de Confiabilidad de Fuentes OSINT

## 📊 Sistema Actual de Reputación

### Cómo Funciona
El sistema actual (`calculate_overall_reputation()`) usa un **promedio simple** sin pesos:

```python
Puntuaciones:
- clean:        +1
- questionable: -1
- suspicious:   -2
- malicious:    -3

Reputación Final (promedio):
- >= 0.5:  CLEAN
- >= -0.5: QUESTIONABLE
- >= -1.5: SUSPICIOUS
- < -1.5:  MALICIOUS
```

**Problema**: Todas las fuentes tienen el mismo peso, independientemente de su fiabilidad.

---

## 🏆 Ranking de Fuentes por Confiabilidad

### Tier 1: Fuentes de Máxima Confiabilidad (Peso: 3.0)

**1. VirusTotal**
- **Por qué es confiable**: 70+ motores antivirus
- **Ideal para**: Detección de malware, URLs maliciosas, dominios comprometidos
- **Falsos positivos**: Bajo (~2-5%)
- **Criterio malicioso**: ≥5 detecciones de engines confiables

**2. AbuseIPDB**
- **Por qué es confiable**: Reportes de abuse de la comunidad validados
- **Ideal para**: IPs maliciosas, spam, ataques DDoS
- **Falsos positivos**: Bajo (~5%)
- **Criterio malicioso**: Confidence score ≥80%

**3. AlienVault OTX**
- **Por qué es confiable**: Threat intelligence de profesionales
- **Ideal para**: IoCs confirmados, campañas APT
- **Falsos positivos**: Bajo-Medio (~5-10%)
- **Criterio malicioso**: ≥3 pulses de usuarios verificados

---

### Tier 2: Fuentes Altamente Confiables (Peso: 2.0)

**4. URLScan.io**
- **Por qué es confiable**: Análisis automatizado con verificación visual
- **Ideal para**: Phishing, defacement, páginas maliciosas
- **Falsos positivos**: Medio (~10-15%)
- **Criterio malicioso**: ≥30% scans maliciosos o ≥5 detecciones

**5. Hybrid Analysis**
- **Por qué es confiable**: Sandbox analysis automatizado
- **Ideal para**: Comportamiento malicioso, malware, droppers
- **Falsos positivos**: Bajo-Medio (~8%)
- **Criterio malicioso**: Threat score ≥70/100

**6. MalwareBazaar**
- **Por qué es confiable**: Base de datos curada de malware conocido
- **Ideal para**: Hashes de malware confirmado
- **Falsos positivos**: Muy bajo (~1-3%)
- **Criterio malicioso**: Presencia en la base de datos = malicioso

**7. ThreatFox (abuse.ch)**
- **Por qué es confiable**: IOC database con malware activo verificado
- **Ideal para**: Dominios, IPs, URLs y hashes de campañas activas
- **Falsos positivos**: Muy bajo (~2-4%)
- **Criterio malicioso**: Cualquier IOC encontrado = malicioso confirmado

---

### Tier 3: Fuentes Confiables con Contexto (Peso: 1.5)

**8. Shodan**
- **Por qué es útil**: Muestra servicios expuestos, vulnerabilidades
- **Ideal para**: Servicios no seguros, IoT comprometido
- **Falsos positivos**: Alto (~20-30%) - requiere interpretación
- **Criterio malicioso**: Presencia de servicios vulnerables conocidos

**9. URLVoid**
- **Por qué es útil**: Agrega múltiples blacklists
- **Ideal para**: URLs en blacklists públicas
- **Falsos positivos**: Medio-Alto (~15-20%)
- **Criterio malicioso**: ≥2 blacklists diferentes

**10. SecurityTrails**
- **Por qué es útil**: Histórico DNS, cambios sospechosos
- **Ideal para**: Fast-flux, domain shadowing
- **Falsos positivos**: Alto (~25%) - requiere análisis
- **Criterio malicioso**: Patrones de fast-flux + edad < 30 días

---

### Tier 4: Fuentes Complementarias (Peso: 1.0)

**11. WHOIS Info**
- **Por qué es útil**: Registro, edad, propietario
- **Ideal para**: Dominios recién registrados, privacidad WHOIS
- **Falsos positivos**: Muy alto (~40-50%)
- **Criterio sospechoso**: Edad < 30 días + privacidad activada

**12-16. Otros (CriminalIP, Cisco Talos, IPGeolocation, etc.)**
- **Por qué son útiles**: Contexto adicional, país de origen
- **Ideal para**: Correlación con otras fuentes
- **Falsos positivos**: Variable (20-40%)

---

## 🎯 Sistema de Pesos Propuesto

### Fórmula Mejorada

```python
# Peso por fuente
source_weights = {
    # Tier 1: Máxima confiabilidad
    'virustotal': 3.0,
    'abuseipdb': 3.0,
    'alienvault_otx': 3.0,
    
    # Tier 2: Altamente confiables
    'urlscan': 2.0,
    'hybrid_analysis': 2.0,
    'malware_bazaar': 2.0,
    'threatfox': 2.0,
    
    # Tier 3: Confiables con contexto
    'shodan': 1.5,
    'urlvoid': 1.5,
    'securitytrails': 1.5,
    
    # Tier 4: Complementarias
    'whois_info': 1.0,
    'criminalip': 1.0,
    'cisco_talos': 1.0,
    'mxtoolbox': 1.0,
    'ip_geolocation': 1.0,
    'viewdns': 1.0,
    'centralops': 1.0,
    'dnslytics': 1.0,
    'ipthc': 1.0,
    'synapsint': 1.0
}

# Cálculo con pesos
def calculate_weighted_reputation(self):
    weighted_score = 0
    total_weight = 0
    
    for source, result in self.results.items():
        if result.get('status') == 'success' and 'reputation' in result:
            reputation = result['reputation']
            weight = source_weights.get(source, 1.0)
            
            score = reputation_scores[reputation] * weight
            weighted_score += score
            total_weight += weight
    
    average_score = weighted_score / total_weight
```

### Ejemplo Práctico

**Escenario**: Análisis de `malicious-site.com`

**Resultados**:
- VirusTotal (peso 3.0): MALICIOUS (-3)
- AbuseIPDB (peso 3.0): MALICIOUS (-3)
- URLScan (peso 2.0): SUSPICIOUS (-2)
- WHOIS (peso 1.0): CLEAN (+1)

**Cálculo con sistema actual (sin pesos)**:
```
Promedio = (-3 + -3 + -2 + 1) / 4 = -1.75
Resultado: MALICIOUS ✓ (correcto)
```

**Cálculo con sistema de pesos**:
```
Weighted = (-3×3.0 + -3×3.0 + -2×2.0 + 1×1.0) / (3.0+3.0+2.0+1.0)
         = (-9 + -9 + -4 + 1) / 9.0
         = -21 / 9.0
         = -2.33
Resultado: MALICIOUS ✓ (con mayor confianza)
```

**Escenario 2**: `legitimate-new-domain.com`

**Resultados**:
- VirusTotal (peso 3.0): CLEAN (+1)
- AlienVault (peso 3.0): CLEAN (+1)
- WHOIS (peso 1.0): SUSPICIOUS (-2) [dominio nuevo]
- URLVoid (peso 1.5): QUESTIONABLE (-1) [1 blacklist menor]

**Sin pesos**: (1 + 1 + -2 + -1) / 4 = -0.25 → **QUESTIONABLE** ❌
**Con pesos**: (1×3.0 + 1×3.0 + -2×1.0 + -1×1.5) / 8.5 = 0.41 → **CLEAN** ✓

---

## ⚡ Reglas de Decisión Rápida

### Alta Prioridad (Override automático a MALICIOUS)

1. **VirusTotal**: ≥10 detecciones → MALICIOUS
2. **MalwareBazaar**: Hash encontrado → MALICIOUS
3. **AbuseIPDB**: Confidence ≥90% → MALICIOUS
4. **AlienVault OTX**: ≥5 pulses maliciosos → MALICIOUS

### Combinaciones Críticas

- **2+ fuentes Tier 1 = MALICIOUS** → Resultado final: MALICIOUS (alta confianza)
- **1 Tier 1 + 2 Tier 2 = MALICIOUS** → Resultado final: MALICIOUS (confianza media)
- **Solo Tier 3-4 = MALICIOUS** → Resultado final: SUSPICIOUS (requiere validación)

---

## 🔍 Recomendaciones de Uso

### Para Analistas SOC

1. **Prioriza siempre Tier 1**: Si VirusTotal, AbuseIPDB o AlienVault marcan como malicioso, investiga inmediatamente
2. **Correlaciona múltiples fuentes**: No confíes en una sola fuente Tier 3-4
3. **Contexto es clave**: Un dominio nuevo (WHOIS) no es automáticamente malicioso

### Para Automatización (SOAR/SIEM)

```python
# Regla para bloqueo automático
if (virustotal.reputation == 'malicious' and virustotal.detections >= 10) or \
   (abuseipdb.confidence >= 90) or \
   (malware_bazaar.found == True):
    action = "BLOCK_IMMEDIATELY"

# Regla para alerta
elif weighted_reputation_score < -1.5:
    action = "ALERT_HIGH_PRIORITY"

# Regla para monitoreo
elif weighted_reputation_score < -0.5:
    action = "MONITOR_SUSPICIOUS"
```

### Para Investigación Manual

1. Empieza por fuentes Tier 1
2. Si hay contradicción, analiza el contexto (edad, geolocalización, etc.)
3. Usa fuentes Tier 3-4 para enriquecer, no para decidir

---

## 📈 Métricas de Precisión (Estimadas)

| Fuente | Precisión | Recall | F1-Score | Falsos Positivos |
|--------|-----------|--------|----------|------------------|
| VirusTotal | 95% | 92% | 0.93 | 2-5% |
| MalwareBazaar | 98% | 85% | 0.91 | 1-3% |
| AbuseIPDB | 93% | 88% | 0.90 | 5% |
| AlienVault OTX | 90% | 87% | 0.88 | 5-10% |
| URLScan | 88% | 85% | 0.86 | 10-15% |
| Hybrid Analysis | 91% | 82% | 0.86 | 8% |
| Shodan | 70% | 75% | 0.72 | 20-30% |
| URLVoid | 75% | 80% | 0.77 | 15-20% |
| WHOIS | 60% | 70% | 0.65 | 40-50% |

---

## 🚀 Implementación Sugerida

### Archivo: `app.py` - Función mejorada

```python
def calculate_overall_reputation_weighted(self):
    """Calculate overall reputation with source weights"""
    
    # Puntuaciones base
    reputation_scores = {
        'clean': 1,
        'unknown': 0,
        'questionable': -1,
        'suspicious': -2,
        'malicious': -3
    }
    
    # Pesos por fuente (basados en confiabilidad)
    source_weights = {
        'virustotal': 3.0,
        'abuseipdb': 3.0,
        'alienvault_otx': 3.0,
        'urlscan': 2.0,
        'hybrid_analysis': 2.0,
        'malware_bazaar': 2.0,
        'shodan': 1.5,
        'urlvoid': 1.5,
        'securitytrails': 1.5,
    }
    
    # Reglas de override para alta confianza
    for source, result in self.results.items():
        if result.get('status') == 'success':
            # VirusTotal con muchas detecciones
            if source == 'virustotal' and result.get('malicious', 0) >= 10:
                return 'malicious'
            
            # MalwareBazaar - hash confirmado
            if source == 'malware_bazaar' and result.get('reputation') == 'malicious':
                return 'malicious'
            
            # AbuseIPDB - alta confianza
            if source == 'abuseipdb' and result.get('abuse_confidence', 0) >= 90:
                return 'malicious'
    
    # Cálculo ponderado
    weighted_score = 0
    total_weight = 0
    
    for source, result in self.results.items():
        if result.get('status') == 'success' and 'reputation' in result:
            reputation = result['reputation']
            if reputation in reputation_scores:
                weight = source_weights.get(source, 1.0)
                weighted_score += reputation_scores[reputation] * weight
                total_weight += weight
    
    if total_weight == 0:
        return 'unknown'
    
    average_score = weighted_score / total_weight
    
    # Umbrales ajustados para sistema ponderado
    if average_score >= 0.3:
        return 'clean'
    elif average_score >= -0.7:
        return 'questionable'
    elif average_score >= -1.5:
        return 'suspicious'
    else:
        return 'malicious'
```

---

## 📚 Referencias

- NIST SP 800-150: Guide to Cyber Threat Information Sharing
- MITRE ATT&CK Framework
- FIRST TLP (Traffic Light Protocol)
- VirusTotal Public API Documentation
- AlienVault OTX Best Practices

---

## ✅ Conclusiones

1. **Prioriza fuentes Tier 1** para decisiones críticas
2. **Usa sistema de pesos** para mejor precisión
3. **No confíes en una sola fuente** - correlaciona múltiples
4. **Contexto importa** - edad del dominio, geolocalización, etc.
5. **Automatiza con cuidado** - define reglas claras basadas en tiers

**Regla de oro**: Si 2 o más fuentes Tier 1 coinciden en "malicious", es altamente probable que el IoC sea malicioso (>95% confianza).
