from fastapi import FastAPI, HTTPException
import requests
import asyncio
import mysql.connector
from mysql.connector import Error

# Configuración de la base de datos (Asegúrate de que la IP sea la correcta)
db_config = {
    "host": "172.16.0.99", 
    "user": "grupo3",
    "password": "1234",
    "database": "citas_medicas"
}

app = FastAPI(title="Gestión de Citas Unificada (Grupos 3.2)")



# Registrar pacientes
@app.post("/pacientes")
def crear_paciente(nombre:str, email:str):
    cursor = conexion.cursor()

    query = "INSERT INTO pacientes (nombre, email) VALUES (%s, %s)"
    cursor.execute(query, (nombre, email))

    conexion.commit()

    return {"mensaje" : "Paciente registrado"}

# Consultar paciente
@app.get("/pacientes/{id}")
def obtener_paciente(id:int):
    cursor = conexion.cursor(dictionary=True)

    query = "SELECT * FROM pacientes WHERE id=%s"

    cursor.execute(query, (id,))

# --- FUNCIÓN GRUPO 3: CREAR CITA ---
@app.post("/citas")
async def crear_cita(paciente_id: int, fecha: str):
    # Validar existencia del paciente consultando al Grupo 2
    # REEMPLAZA 'IP_GRUPO2' por la IP real del compañero que tiene el Servicio de Consulta
    try:
        r = requests.get(f"http://172.16.0.99:8003/pacientes/{paciente_id}", timeout=5)
        if r.status_code != 200:
            raise HTTPException(status_code=404, detail="El paciente no existe en el sistema")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Servicio de Consulta de Pacientes no disponible")

    # Simulación de sección crítica / carga procesada
    await asyncio.sleep(2)

    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()

        query = "INSERT INTO citas (paciente_id, fecha, estado) VALUES (%s, %s, 'activa')"

        cursor.execute(query, (paciente_id, fecha))

        conexion.commit()

        nuevo_id = cursor.lastrowid

        cursor.close()
        conexion.close()
        return {"mensaje": "Cita creada correctamente", "id_cita": nuevo_id}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error de DB: {e}")

# --- FUNCIÓN GRUPO 3: CONSULTAR CITAS ---
@app.get("/citas/{paciente_id}")
def listar_citas(paciente_id: int):
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor(dictionary=True)
        query = "SELECT * FROM citas WHERE paciente_id = %s"
        cursor.execute(query, (paciente_id,))
        citas = cursor.fetchall()
        cursor.close()
        conexion.close()
        return citas
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error de DB: {e}")

# --- FUNCIÓN GRUPO 5: CANCELAR CITA ---
@app.delete("/citas/{id}")
def cancelar_cita(id: int):
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()
        
        # Verificamos si existe antes de actualizar
        cursor.execute("SELECT id FROM citas WHERE id = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conexion.close()
            raise HTTPException(status_code=404, detail="La cita no existe")

        query = "UPDATE citas SET estado = 'cancelada' WHERE id = %s"
        cursor.execute(query, (id,))
        conexion.commit()
        cursor.close()
        conexion.close()
        return {"mensaje": "Cita cancelada exitosamente"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Error de DB: {e}")

# --- INICIO DEL SERVIDOR (UNIFICADO EN PUERTO 8003) ---
if _name_ == "_main_":
    import uvicorn
    # Ahora todo corre en el puerto 8003
    uvicorn.run(app, host="0.0.0.0", port=8003)