# 🧩 Plan de Recuperación de Desastres — Base de Datos (Cloud SQL)

Este procedimiento describe cómo restaurar la base de datos de producción en caso de pérdida de datos o error crítico.

---

## 1️⃣ Clonar la instancia desde un punto anterior en el tiempo

1. En la **Consola de Google Cloud**, ve a  
   **SQL → Tu instancia de producción**.
2. En la parte superior, haz clic en **CLONAR**.
3. Configura el clon:
   - **ID de la instancia:** `fastdiet-db-recuperada-YYYYMMDD`.
   - **Fuente:** “Clonar desde un punto anterior en el tiempo”.
   - **Punto en el tiempo (UTC):** selecciona la hora **justo antes** del incidente.
4. Haz clic en **CREAR CLON** y espera unos minutos a que se complete el proceso.

---

## 2️⃣ Verificar la integridad del clon

Conéctate a la instancia restaurada:

    gcloud sql connect fastdiet-db-recuperada-YYYYMMDD --user=root

Dentro del cliente MySQL:

    USE fastdiet_prod_db;

    -- Verifica que las tablas y datos estén presentes
    SELECT COUNT(*) FROM meal_plans;
    SELECT * FROM users WHERE email = 'usuario.afectado@email.com';

Si los datos son correctos, procede a redirigir la aplicación.

---

## 3️⃣ Redirigir el backend (Cloud Run) al clon

1. Ve a **Cloud Run → Servicio del backend**.  
2. Haz clic en **EDITAR E IMPLEMENTAR NUEVA REVISIÓN**.  
3. En la pestaña **Conexiones**, elimina la conexión antigua y añade la nueva instancia clonada.  
4. Haz clic en **IMPLEMENTAR**.  
   > Esto desplegará una nueva revisión conectada a la base restaurada.

---

## 4️⃣ Verificación final

- **Prueba la app:** Abre la app o usa Postman para comprobar lectura y escritura.  
- **Revisa los logs:** En Cloud Run → pestaña **Registros**, confirma que no haya errores de conexión.

---

## 5️⃣ Limpieza (tras 24–48h)

1. Detén la instancia original desde Cloud SQL (para reducir costes).  
2. Verifica durante uno o dos días que la app funciona correctamente.  
3. Cuando todo esté estable, elimina la instancia dañada de forma segura.

