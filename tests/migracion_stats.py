"""
Migración de las citas para estadísticas de la versión 1.0 a la actual versión 2.0
"""

import argparse
import logging
import os
import csv
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import text, create_engine
from lib.safe_string import safe_string

from citas_admin.app import create_app
from citas_admin.extensions import db

from citas_admin.blueprints.cit_clientes.models import CitCliente
from citas_admin.blueprints.cit_servicios.models import CitServicio
from citas_admin.blueprints.oficinas.models import Oficina
from citas_admin.blueprints.cit_citas.models import CitCita

OFICINAS_CSV = "seed/oficinas_v1_v2.csv"
SERVICIOS_CSV = "seed/servicios_v1_v2.csv"
CLIENTE_NO_DEFINIDO_EMAIL = "no_definido@nodefinido.com"
CLIENTE_ID_NO_DEFINIDO = 0
TOTAL_CITAS_V1 = 274661


def main():
    """Main function"""

    # Inicializar
    load_dotenv()  # Take environment variables from .env
    app = create_app()
    db.app = app

    # Manejo de un Log
    bitacora = logging.getLogger("migracion")
    bitacora.setLevel(logging.INFO)
    formato = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    empunadura = logging.FileHandler("migracion_stats.log")
    empunadura.setFormatter(formato)
    bitacora.addHandler(empunadura)

    # -- Crear conexión a la BD v1 MySQL
    load_dotenv(".env")  # Se necesita un arhivo .env local para cargar la variable de la BD v1
    ENGINE_V1 = os.getenv("ENGINE_V1", "")  # Ruta de conexión de la BD V1.
    engine = create_engine(ENGINE_V1)

    # Simulación o ejecución
    simulacion = True
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--exec", help="Ejecutar cambio en la BD", action="store_true")
    args = parser.parse_args()
    if args.exec:
        simulacion = False

    # -- Migración de las Tablas --
    with engine.connect() as connection:
        print("=== Migración de citas para estadísticas ===")
        counts = {
            "cliente_no_encontrado": 0,
            "exito": 0,
        }
        # Hacemos hincapié si estamos en Prueba o Ejecución
        if simulacion:
            print("-MODO PRUEBA-")
        else:
            print("-MODO EJECUCIÓN-")
        # Carga de la relación de Juzgados_id --> Oficinas_id
        ruta = Path(OFICINAS_CSV)
        if not ruta.exists():
            bitacora.warning(f"No se econtró el archivo {ruta.name}")
            print(f"AVISO: {ruta.name} no se encontró.")
            return
        if not ruta.is_file():
            bitacora.warning(f"No se es un archivo {ruta.name}")
            print(f"AVISO: {ruta.name} no es un archivo.")
            return
        oficinas = {}
        with open(ruta, encoding="utf-8") as puntero:
            rows = csv.DictReader(puntero)
            for row in rows:
                oficinas[int(row["id_juzgado_v1"])] = {
                    "id_oficina_v2": int(row["id_oficina_v2"]),
                    "nombre": row["nombre"],
                }
        print(f"Oficinas cargadas: {len(oficinas)}")
        # Carga de la relación de Servicios
        ruta = Path(SERVICIOS_CSV)
        if not ruta.exists():
            bitacora.warning(f"No se econtró el archivo {ruta.name}")
            print(f"AVISO: {ruta.name} no se encontró.")
            return
        if not ruta.is_file():
            bitacora.warning(f"No se es un archivo {ruta.name}")
            print(f"AVISO: {ruta.name} no es un archivo.")
            return
        servicios = {}
        with open(ruta, encoding="utf-8") as puntero:
            rows = csv.DictReader(puntero)
            for row in rows:
                servicios[int(row["id_v1"])] = {
                    "id_servicio_v2": int(row["id_v2"]),
                    "nombre": row["descripcion"],
                    "duracion": int(row["duracion"]),
                }
        print(f"Servicios cargados: {len(servicios)}")
        # Buscar la definición del cliente NO DEFINIDO en la ver. 2.
        if definir_cliente_no_definido() == False:
            msg = "No se econtró la declaración de un cliente NO DEFINIDO en la versión 2"
            bitacora.warning(msg)
            print(f"ERROR: {msg}")
            return

        citas_v1 = connection.execute(text("SELECT * FROM citas WHERE fecha < '2022-08-01'"))
        for cita_v1 in citas_v1:
            juzgado_id_v1 = 507
            servicio_id_v1 = 0
            if cita_v1["id_juzgado"] is not None:
                juzgado_id_v1 = cita_v1["id_juzgado"]
            if cita_v1["id_servicio"] is not None:
                servicio_id_v1 = cita_v1["id_servicio"]
            # establecer fecha de inicio y termino
            fecha_inicio = datetime.strptime(f"{cita_v1['fecha']} {cita_v1['hora']}", "%Y-%m-%d %H:%M:00")
            fecha_termino = fecha_inicio + timedelta(minutes=servicios[servicio_id_v1]["duracion"])
            # Buscar coincidencia del cliente
            cliente_id = encontrar_cliente(cita_v1["correo"])
            if cliente_id == CLIENTE_ID_NO_DEFINIDO:
                counts["cliente_no_encontrado"] += 1
            # Impresión de muestras
            if counts["exito"] % 888 == 0:
                print("citas insertadas {:,}, {}%".format(counts["exito"], round((counts["exito"] * 100) / TOTAL_CITAS_V1)))
            # Hacer el insert en BD v2
            if simulacion == False:
                CitCita(
                    creado=cita_v1["alta_fecha"],
                    modificado=cita_v1["alta_fecha"],
                    cit_cliente_id=cliente_id,
                    cit_servicio_id=servicios[servicio_id_v1]["id_servicio_v2"],
                    oficina_id=oficinas[juzgado_id_v1]["id_oficina_v2"],
                    inicio=fecha_inicio,
                    termino=fecha_termino,
                    codigo_asistencia="0000",
                    estado="PENDIENTE",
                    asistencia=False,
                ).save()

            counts["exito"] += 1
        # Da el total de errores encontrados
        mensaje_final = f"Total de citas insertadas {counts['exito']}, "
        mensaje_final = mensaje_final + f"clientes NO DEFINIDOS:{counts['cliente_no_encontrado']} "
        bitacora.info(mensaje_final)
        print(mensaje_final)


def definir_cliente_no_definido():
    """Busca el registro del cliente no definido en la versión 2 y lo guarda en variable"""
    cliente = CitCliente.query.filter_by(email=CLIENTE_NO_DEFINIDO_EMAIL).first()
    if cliente:
        global CLIENTE_ID_NO_DEFINIDO
        CLIENTE_ID_NO_DEFINIDO = cliente.id
        return True
    return False


def encontrar_cliente(email):
    """Busca el email de un cliente y regresa su id se lo encontró"""
    cliente = CitCliente.query.filter_by(email=email).first()
    if cliente:
        return cliente.id
    return CLIENTE_ID_NO_DEFINIDO


if __name__ == "__main__":
    main()
