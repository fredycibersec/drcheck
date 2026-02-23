# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir a Domain Reputation WebApp! Este documento te guiará en el proceso de contribución.

## 📋 Código de Conducta

- Sé respetuoso y profesional en todas las interacciones
- Acepta críticas constructivas con apertura
- Enfócate en lo que es mejor para la comunidad
- Muestra empatía hacia otros miembros de la comunidad

## 🚀 ¿Cómo Puedo Contribuir?

### Reportar Bugs

Si encuentras un bug, por favor abre un issue con:

- **Título descriptivo** que identifique el problema
- **Descripción detallada** del comportamiento esperado vs actual
- **Pasos para reproducir** el bug
- **Capturas de pantalla** si es relevante
- **Entorno:** versión de Python, SO, navegador, etc.
- **Logs de error** si están disponibles

### Sugerir Mejoras

Para sugerir nuevas funcionalidades:

1. Verifica que no exista ya un issue similar
2. Abre un nuevo issue con la etiqueta `enhancement`
3. Describe claramente:
   - El problema que resuelve
   - La solución propuesta
   - Alternativas consideradas
   - Impacto en el proyecto

### Pull Requests

#### Proceso

1. **Fork** el repositorio
2. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```
3. **Implementa** tus cambios siguiendo las guías de estilo
4. **Añade tests** si aplica
5. **Actualiza documentación** si es necesario
6. **Commit** con mensajes claros:
   ```bash
   git commit -m "Add: nueva funcionalidad X"
   git commit -m "Fix: corregido bug en Y"
   git commit -m "Docs: actualizada documentación de Z"
   ```
7. **Push** a tu fork:
   ```bash
   git push origin feature/nombre-descriptivo
   ```
8. **Abre un Pull Request** en GitHub

#### Convenciones de Commits

Usa prefijos descriptivos:

- `Add:` - Nueva funcionalidad
- `Fix:` - Corrección de bug
- `Update:` - Actualización de funcionalidad existente
- `Refactor:` - Refactorización de código
- `Docs:` - Cambios en documentación
- `Style:` - Cambios de formato (sin afectar funcionalidad)
- `Test:` - Añadir o modificar tests
- `Chore:` - Tareas de mantenimiento

#### Ejemplo de Buen Commit
```
Add: integración con API de GreyNoise

- Añadida nueva fuente Tier 2 para análisis de IPs
- Implementado endpoint /api/greynoise
- Actualizado sistema de scoring para incluir GreyNoise
- Añadida documentación de la nueva API
```

## 🎨 Guías de Estilo

### Python

- Sigue [PEP 8](https://pep8.org/)
- Usa 4 espacios para indentación (no tabs)
- Longitud máxima de línea: 100 caracteres
- Docstrings para todas las funciones públicas
- Type hints cuando sea posible

```python
def analyze_domain(domain: str, api_key: str) -> dict:
    """
    Analiza la reputación de un dominio.
    
    Args:
        domain: El dominio a analizar (ej: example.com)
        api_key: API key para autenticación
        
    Returns:
        dict: Resultados del análisis con scores y detecciones
    """
    pass
```

### JavaScript

- Usa ES6+ features
- 2 espacios para indentación
- Camel case para variables y funciones
- JSDoc para funciones complejas
- Usa `const` y `let`, nunca `var`

```javascript
/**
 * Fetch domain reputation from backend
 * @param {string} domain - Domain to analyze
 * @returns {Promise<Object>} Analysis results
 */
async function fetchDomainReputation(domain) {
    const response = await fetch(`/api/analyze?domain=${domain}`);
    return response.json();
}
```

### HTML/CSS

- Indentación consistente (2 espacios)
- Usa variables CSS para colores y espaciados
- Clases semánticas (no `.red-text`, sí `.error-message`)
- HTML semántico (usa `<header>`, `<nav>`, `<section>`, etc.)

## 🧪 Tests

- Añade tests para nuevas funcionalidades
- Asegúrate de que los tests existentes pasan
- Cubre casos edge y manejo de errores

```python
def test_domain_reputation_malicious():
    """Test que un dominio conocido como malicioso se clasifica correctamente"""
    result = analyze_domain('malicious.example.com')
    assert result['reputation'] == 'malicious'
    assert result['score'] < -1.5
```

## 📚 Documentación

Al añadir nuevas funcionalidades:

1. Actualiza el `README.md` si es necesario
2. Añade comentarios en el código
3. Actualiza archivos en `/docs` si aplica
4. Documenta nuevas APIs o configuraciones

## 🏗️ Áreas de Contribución Prioritarias

### Alta Prioridad
- ✅ Integración con nuevas fuentes de threat intelligence
- ✅ Optimización de rendimiento
- ✅ Mejoras en el sistema de scoring
- ✅ Tests automatizados
- ✅ Documentación de APIs

### Media Prioridad
- 🟡 Nuevas visualizaciones de datos
- 🟡 Exportación de reportes (PDF, CSV)
- 🟡 Soporte para más tipos de búsqueda
- 🟡 Integración con otras herramientas OSINT
- 🟡 Mejoras en la UI/UX

### Baja Prioridad
- 🟢 Traducciones a otros idiomas
- 🟢 Temas adicionales
- 🟢 Shortcuts de teclado
- 🟢 Modo offline

## ❓ ¿Tienes Preguntas?

Si tienes dudas sobre cómo contribuir:

1. Revisa los [issues existentes](https://github.com/tu-usuario/Domain-Reputation-WebApp/issues)
2. Busca en las [discusiones](https://github.com/tu-usuario/Domain-Reputation-WebApp/discussions)
3. Abre un nuevo issue con la etiqueta `question`

## 🙏 Reconocimiento

Todos los contribuidores serán reconocidos en el README y en la sección "About" de la aplicación.

¡Gracias por hacer de este proyecto algo mejor! 🎉
