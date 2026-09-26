#!/usr/bin/env python3
"""
Script para generar un paquete instalador Debian/Ubuntu (.deb) para proyecto2.py
Totalmente compatible con Debian, Ubuntu, Linux Mint, Pop!_OS, etc.
"""

import io
import os
import sys
import time
import tarfile
import hashlib
from pathlib import PurePosixPath

# ==============================================================================
# CONFIGURACIÓN DEL PAQUETE
# ==============================================================================
PACKAGE_NAME = "proyecto2"
VERSION = "1.0.0"
ARCHITECTURE = "all"
MAINTAINER = "Universidad de Costa Rica <ucr@ucr.ac.cr>"
SECTION = "math"
PRIORITY = "optional"
DEPENDS = "python3, python3-tk, python3-numpy, python3-sympy, python3-matplotlib"
DESCRIPTION = """Capacidad de Servidores y Costo Marginal (UCR)
 Prototipo interactivo con tooltips, explicaciones pedagogicas y
 presets dinamicos para MA-0321 Calculo Diferencial e Integral.
 Desarrollado para la Escuela de Matematica de la UCR."""

LAUNCHER_SCRIPT = """#!/bin/sh
exec python3 /usr/share/proyecto2/proyecto2.py "$@"
"""

DESKTOP_ENTRY = """[Desktop Entry]
Version=1.0
Type=Application
Name=Proyecto 2 - Cálculo UCR
GenericName=Capacidad de Servidores y Costo Marginal
Comment=Herramienta interactiva de optimización y costo marginal (MA-0321)
Exec=proyecto2
Icon=utilities-system-monitor
Terminal=false
Categories=Education;Science;Math;
StartupNotify=true
"""

def make_ar_header(name: str, size: int, mtime: int = None, mode: int = 0o100644, uid: int = 0, gid: int = 0) -> bytes:
    if mtime is None:
        mtime = int(time.time())
    name_bytes = name.encode('ascii')[:16].ljust(16, b' ')
    mtime_bytes = str(mtime).encode('ascii')[:12].ljust(12, b' ')
    uid_bytes = str(uid).encode('ascii')[:6].ljust(6, b' ')
    gid_bytes = str(gid).encode('ascii')[:6].ljust(6, b' ')
    mode_bytes = oct(mode)[2:].encode('ascii')[:8].ljust(8, b' ')
    size_bytes = str(size).encode('ascii')[:10].ljust(10, b' ')
    magic = b"`\n"
    res = name_bytes + mtime_bytes + uid_bytes + gid_bytes + mode_bytes + size_bytes + magic
    assert len(res) == 60, f"Error en encabezado AR: longitud {len(res)}"
    return res

def pack_ar(members: list[tuple[str, bytes]]) -> bytes:
    out = io.BytesIO()
    out.write(b"!<arch>\n")
    for name, content in members:
        hdr = make_ar_header(name, len(content))
        out.write(hdr)
        out.write(content)
        if len(content) % 2 != 0:
            out.write(b"\n")
    return out.getvalue()

def build_deb(output_deb_path: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    py_file = os.path.join(base_dir, "proyecto2.py")
    if not os.path.exists(py_file):
        raise FileNotFoundError(f"No se encontró {py_file}")

    with open(py_file, "rb") as f:
        py_content = f.read()

    # Asegurar saltos de línea LF en el script de python y launcher
    py_content = py_content.replace(b"\r\n", b"\n")
    launcher_bytes = LAUNCHER_SCRIPT.replace("\r\n", "\n").encode("utf-8")
    desktop_bytes = DESKTOP_ENTRY.replace("\r\n", "\n").encode("utf-8")

    current_time = int(time.time())

    # 1. Crear data.tar.gz
    data_io = io.BytesIO()
    md5sums_lines = []

    def add_data_file(tar, path_str, content_bytes, mode=0o644):
        # path_str relative to /: e.g. "usr/bin/proyecto2"
        ti = tarfile.TarInfo(name=f"./{path_str}")
        ti.type = tarfile.REGTYPE
        ti.size = len(content_bytes)
        ti.mtime = current_time
        ti.mode = mode
        ti.uname = "root"
        ti.gname = "root"
        ti.uid = 0
        ti.gid = 0
        tar.addfile(ti, io.BytesIO(content_bytes))
        
        digest = hashlib.md5(content_bytes).hexdigest()
        md5sums_lines.append(f"{digest}  {path_str}\n")

    def add_data_dir(tar, dir_str):
        ti = tarfile.TarInfo(name=f"./{dir_str}")
        ti.type = tarfile.DIRTYPE
        ti.size = 0
        ti.mtime = current_time
        ti.mode = 0o755
        ti.uname = "root"
        ti.gname = "root"
        ti.uid = 0
        ti.gid = 0
        tar.addfile(ti)

    with tarfile.open(fileobj=data_io, mode="w:gz", format=tarfile.GNU_FORMAT) as data_tar:
        # Directorios
        for d in [
            "usr",
            "usr/bin",
            "usr/share",
            "usr/share/proyecto2",
            "usr/share/applications",
        ]:
            add_data_dir(data_tar, d)

        # Archivos
        add_data_file(data_tar, "usr/bin/proyecto2", launcher_bytes, mode=0o755)
        add_data_file(data_tar, "usr/share/proyecto2/proyecto2.py", py_content, mode=0o755)
        add_data_file(data_tar, "usr/share/applications/proyecto2.desktop", desktop_bytes, mode=0o644)

        # Si existe el gráfico de utilidad, incluirlo
        grafico_path = os.path.join(base_dir, "grafico_utilidad.png")
        if os.path.exists(grafico_path):
            with open(grafico_path, "rb") as gf:
                add_data_file(data_tar, "usr/share/proyecto2/grafico_utilidad.png", gf.read(), mode=0o644)

    data_tar_bytes = data_io.getvalue()

    # 2. Crear control.tar.gz
    control_content = f"""Package: {PACKAGE_NAME}
Version: {VERSION}
Section: {SECTION}
Priority: {PRIORITY}
Architecture: {ARCHITECTURE}
Depends: {DEPENDS}
Installed-Size: {int(len(py_content) / 1024) + 10}
Maintainer: {MAINTAINER}
Description: {DESCRIPTION}
"""
    control_bytes = control_content.replace("\r\n", "\n").encode("utf-8")
    md5sums_bytes = "".join(md5sums_lines).encode("utf-8")

    control_io = io.BytesIO()
    with tarfile.open(fileobj=control_io, mode="w:gz", format=tarfile.GNU_FORMAT) as ctar:
        # ./control
        ti_c = tarfile.TarInfo(name="./control")
        ti_c.type = tarfile.REGTYPE
        ti_c.size = len(control_bytes)
        ti_c.mtime = current_time
        ti_c.mode = 0o644
        ti_c.uname = "root"
        ti_c.gname = "root"
        ctar.addfile(ti_c, io.BytesIO(control_bytes))

        # ./md5sums
        ti_m = tarfile.TarInfo(name="./md5sums")
        ti_m.type = tarfile.REGTYPE
        ti_m.size = len(md5sums_bytes)
        ti_m.mtime = current_time
        ti_m.mode = 0o644
        ti_m.uname = "root"
        ti_m.gname = "root"
        ctar.addfile(ti_m, io.BytesIO(md5sums_bytes))

    control_tar_bytes = control_io.getvalue()

    # 3. Empaquetar todo en formato AR (.deb)
    # Según estándar Debian:
    # 1) debian-binary (2.0\n)
    # 2) control.tar.gz
    # 3) data.tar.gz
    deb_bytes = pack_ar([
        ("debian-binary", b"2.0\n"),
        ("control.tar.gz", control_tar_bytes),
        ("data.tar.gz", data_tar_bytes),
    ])

    with open(output_deb_path, "wb") as f:
        f.write(deb_bytes)

    print(f"[OK] Paquete Debian creado exitosamente: {output_deb_path}")
    print(f"     Tamaño: {len(deb_bytes):,} bytes")

if __name__ == "__main__":
    out_name = f"{PACKAGE_NAME}_{VERSION}_all.deb"
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), out_name)
    build_deb(out_path)
