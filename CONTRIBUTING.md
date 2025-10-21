# 🧭 Guía de Contribución

Este proyecto utiliza un flujo de trabajo basado en **Git** y **GitHub** con integración mediante *Pull Requests (PRs)*.  
El objetivo es mantener un historial limpio, estable y colaborativo.

---

## 🪴 Ramas principales

| Rama | Descripción |
|------|--------------|
| `main` | Versión estable del proyecto. Solo se actualiza desde `dev`. |
| `dev` | Rama base de desarrollo. Recibes **solo merges** desde ramas `feature/*` y `fix/*`. |
| `feature/*` | Ramas para nuevas funcionalidades. |
| `fix/*` | Ramas para correcciones de bugs o mejoras pequeñas. |

---

## 🚀 Flujo de trabajo

### 1️⃣ Crear una nueva rama
Crea tu rama desde `dev`:

```bash
git checkout dev
git pull origin dev
# para nuevas funcionalidades
git checkout -b feature/nombre-funcionalidad
# o para correcciones
git checkout -b fix/nombre-correcion
```

### 2️⃣ Realiza tus cambios y commits
Realiza tus cambios en la nueva rama. Realiza commits pequeños y con una sola responsabilidad.
```bash
git add .
git commit -m "Descripción clara y descriptiva de los cambios"
```

### Si necesitas actualizar tu rama con los últimos cambios de `dev`:
La rama `dev` puede haber cambiado desde que creaste tu rama. Actualiza tu rama con:
```bash
# Solo si no estás en tu rama de trabajo
git checkout feature/nombre-funcionalidad  # o fix/nombre-correcion
git pull origin dev
```


### 3️⃣ Haz tu PR hacia `dev`
Una vez que terminaste de realizar tus cambios en la rama crea un PR hacia `dev`.

Asegúrate de que tu rama esté actualizada con `dev` antes de hacer el PR. **No realizar esto puede eliminar cambios de otros colaboradores**:

```bash
git pull origin dev
git push origin feature/nombre-funcionalidad
```

Si hay conflictos, resuélvelos localmente antes de hacer el push.

> [!CAUTION]
> La rama `dev` es la única que recibe merges directos desde otras ramas. Una rama `feature/*` o `fix/*` nunca debe hacer merge directo a `main` ni a otra rama `feature/*` o `fix/*`.

### 4️⃣ Revisión y Merge
Tu PR será revisado por otros colaboradores. Una vez aprobado, se hará el merge a `dev`.

### 5️⃣ Actualiza tu rama local
Después de que tu PR haya sido mergeado, asegúrate de actualizar tu rama local:

```bash
git checkout dev
git pull origin dev
```
