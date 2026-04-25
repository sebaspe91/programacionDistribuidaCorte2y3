"""
Pruebas del sistema de citas médicas.
(La API y los servicios deben estar corriendo)
"""
import requests
import json

BASE = "http://127.0.0.1:8006"


def separador(titulo):
    print(f"\n{'='*55}")
    print(f"  {titulo}")
    print('='*55)


def test(descripcion, response, esperado_status=200):
    ok = response.status_code == esperado_status
    estado = "✅ PASS" if ok else "❌ FAIL"
    print(f"{estado} [{response.status_code}] {descripcion}")
    try:
        print(f"       → {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception:
        print(f"       → {response.text}")
    return ok


# ── 1. Crear cita simple ───────────────────────────────────────────────────
separador("1. Crear cita simple")

test(
    "Crear cita en 10am para Juan",
    requests.post(f"{BASE}/crear_cita", json={"horario": "10am", "paciente": "Juan Pérez"}),
)

test(
    "Crear cita en 10am nuevamente (debe fallar - horario ocupado)",
    requests.post(f"{BASE}/crear_cita", json={"horario": "10am", "paciente": "María López"}),
    esperado_status=400,
)

test(
    "Crear cita en 11am para María",
    requests.post(f"{BASE}/crear_cita", json={"horario": "11am", "paciente": "María López"}),
)

# ── 2. Múltiples horarios ──────────────────────────────────────────────────
separador("2. Crear múltiples citas a la vez")

test(
    "Crear citas en 2pm, 3pm, 4pm para Carlos",
    requests.post(f"{BASE}/crear_citas_multiples", json={
        "horarios": ["2pm", "3pm", "4pm"],
        "paciente": "Carlos Ruiz",
    }),
)

test(
    "Intentar crear citas con horarios ya ocupados (2pm, 5pm)",
    requests.post(f"{BASE}/crear_citas_multiples", json={
        "horarios": ["2pm", "5pm"],
        "paciente": "Ana Gómez",
    }),
)

# ── 3. Listar citas ────────────────────────────────────────────────────────
separador("3. Listar citas activas")

test(
    "Listar todas las citas activas",
    requests.get(f"{BASE}/citas/activas"),
)

# ── 4. Cancelar cita ───────────────────────────────────────────────────────
separador("4. Cancelar cita")

test(
    "Cancelar cita en 11am",
    requests.delete(f"{BASE}/cancelar_cita?horario=11am"),
)

test(
    "Cancelar cita ya cancelada (debe fallar)",
    requests.delete(f"{BASE}/cancelar_cita?horario=11am"),
    esperado_status=400,
)

test(
    "Cancelar cita inexistente (debe fallar)",
    requests.delete(f"{BASE}/cancelar_cita?horario=99pm"),
    esperado_status=404,
)

# ── 5. Listar todas ────────────────────────────────────────────────────────
separador("5. Listar todas las citas (activas + canceladas)")

test(
    "Listar todas las citas",
    requests.get(f"{BASE}/citas"),
)

# ── 6. Logs ────────────────────────────────────────────────────────────────
separador("6. Ver logs del sistema")

test(
    "Ver log de eventos",
    requests.get(f"{BASE}/logs"),
)

print(f"\n{'='*55}")
print("  Pruebas completadas.")
print('='*55)