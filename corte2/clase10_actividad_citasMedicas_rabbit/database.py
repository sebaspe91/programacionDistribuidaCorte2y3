import sqlite3
import threading
from datetime import datetime

DB_PATH = "citas.db"

# Lock para operaciones thread-safe en SQLite
_lock = threading.Lock()


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas si no existen."""
    with _lock:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                horario     TEXT    NOT NULL UNIQUE,
                paciente    TEXT    NOT NULL,
                estado      TEXT    NOT NULL DEFAULT 'activa',
                creada_en   TEXT    NOT NULL,
                cancelada_en TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                evento      TEXT    NOT NULL,
                detalle     TEXT,
                fecha       TEXT    NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    print("[DB] Base de datos inicializada.")


# ── Citas ──────────────────────────────────────────────────────────────────

def guardar_cita(horario: str, paciente: str) -> bool:
    """Inserta una cita. Devuelve True si fue exitosa, False si ya existe."""
    with _lock:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO citas (horario, paciente, estado, creada_en) VALUES (?,?,?,?)",
                (horario, paciente, "activa", datetime.now().isoformat()),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()


def cancelar_cita(horario: str) -> bool:
    """Marca una cita como cancelada. Devuelve True si existía y estaba activa."""
    with _lock:
        conn = get_connection()
        cursor = conn.execute(
            "UPDATE citas SET estado='cancelada', cancelada_en=? WHERE horario=? AND estado='activa'",
            (datetime.now().isoformat(), horario),
        )
        conn.commit()
        afectadas = cursor.rowcount
        conn.close()
        return afectadas > 0


def listar_citas(solo_activas: bool = False) -> list:
    with _lock:
        conn = get_connection()
        if solo_activas:
            rows = conn.execute(
                "SELECT * FROM citas WHERE estado='activa' ORDER BY creada_en"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM citas ORDER BY creada_en"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


def obtener_cita(horario: str) -> dict | None:
    with _lock:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM citas WHERE horario=?", (horario,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None


# ── Logs ───────────────────────────────────────────────────────────────────

def guardar_log(evento: str, detalle: str = ""):
    with _lock:
        conn = get_connection()
        conn.execute(
            "INSERT INTO logs (evento, detalle, fecha) VALUES (?,?,?)",
            (evento, detalle, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()


def listar_logs() -> list:
    with _lock:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM logs ORDER BY fecha DESC LIMIT 100"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]