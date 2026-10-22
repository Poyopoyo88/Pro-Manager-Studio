# Guía de contribución

## Ramas

| Rama | Uso |
|---|---|
| `main` | Versión estable. Solo recibe fusiones desde `develop` mediante *pull request*. |
| `develop` | Integración del trabajo en curso. |
| `feature/HU-XX-descripcion` | Una historia de usuario o mejora. Sale de `develop` y vuelve a `develop`. |
| `fix/descripcion` | Corrección de un error. |

```bash
git checkout develop
git pull
git checkout -b feature/HU-02-cantera
# ... trabajo con TDD ...
git push -u origin feature/HU-02-cantera
# Abre la pull request hacia develop en GitHub
```

## Mensajes de commit

Formato corto en español, en modo imperativo, con prefijo de tipo:

```text
feat(vestuario): agrega ruedas de prensa
fix(partido): impide sustituir a un expulsado
test(club): cubre el límite exacto de masa salarial
docs: actualiza la matriz de trazabilidad
refactor(simulador): extrae el cálculo de fuerza por línea
```

## Ciclo de trabajo (TDD)

1. **Red:** escribe la prueba que describe la regla y comprueba que falla.
2. **Green:** escribe el código mínimo para que pase.
3. **Refactor:** limpia sin cambiar el comportamiento; las pruebas deben seguir en verde.

Antes de abrir la PR:

```bash
pytest --cov
ruff check .
ruff format .
```

## Reglas de arquitectura

- Las reglas de negocio van en `src/pro_manager/dominio/`. Ese paquete **no** importa
  FastAPI, Pydantic ni otras capas (lo verifica `tests/unitarias/test_arquitectura.py`).
- Los controladores de `aplicacion/` coordinan; no deciden reglas.
- Cada error de negocio es una subclase de `ErrorDominio` con su `codigo`; la API lo
  traduce a HTTP automáticamente.

## Revisión de código obligatoria (configurar una sola vez en GitHub)

1. En el repositorio: **Settings → Branches → Add branch ruleset** (o *Add rule*).
2. Aplica la regla a `main` y a `develop`.
3. Activa:
   - **Require a pull request before merging**, con al menos **1 approval**.
   - **Require review from Code Owners** (usa `.github/CODEOWNERS`).
   - **Require status checks to pass** y elige los checks `Quality Gate (Python 3.11)`,
     `Quality Gate (Python 3.12)` y `Quality Gate (Python 3.13)`.
   - **Block force pushes**.

Los checks aparecen en la lista después de la primera ejecución del flujo de CI.

## Cómo revisar una PR

- ¿La regla de negocio tiene prueba y vive en el dominio?
- ¿Los nombres y mensajes están en español y son claros para el usuario?
- ¿Se actualizó la documentación de `docs/` si cambió el comportamiento?
- ¿La cobertura se mantuvo por encima del 80 %?
