# Guía de Instalación y Uso en Linux (Ubuntu, Debian, Mint, Pop!_OS, etc.)

---

## 🚀 Instalación mediante el paquete `.deb`

Tienes a disposición el paquete oficial: **`proyecto2_1.0.0_all.deb`**.

### Método 1: Gráfico (Doble clic)
1. Haz **doble clic** sobre el archivo `proyecto2_1.0.0_all.deb`.
2. Se abrirá la tienda o gestor de software del sistema (Ubuntu Software, Discover o GDebi).
3. Haz clic en **Instalar**.

### Método 2: Terminal
Abre una terminal en la carpeta donde está el archivo `.deb` y ejecuta:
```bash
sudo apt install ./proyecto2_1.0.0_all.deb
```
*(Al usar `apt install ./...`, el sistema resuelve y descarga automáticamente las librerías necesarias como `python3-tk`, `matplotlib`, `sympy` y `numpy`).*

---

## 🖥️ Cómo abrir la aplicación

- **Desde el menú de aplicaciones:** Búscalo con el nombre **"Proyecto 2 - Cálculo UCR"**.
- **Desde la terminal:** Escribe simplemente:
  ```bash
  proyecto2
  ```

---

## 🗑️ Cómo desinstalar la aplicación

```bash
sudo apt remove proyecto2
```

---

## 📦 Cómo volver a generar el `.deb` tras cambios en el código

Si modificas `proyecto2.py`, ejecuta en la terminal:
```bash
python crear_deb.py
```
Y se regenerará el archivo `proyecto2_1.0.0_all.deb` actualizado.
