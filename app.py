from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

app = Flask(__name__)
app.secret_key = "clave_secreta_super_segura"

# =========================
# CONFIGURACIÓN CLOUDINARY
# =========================
# 👉 CONFIGURA TUS CREDENCIALES DE CLOUDINARY AQUÍ
cloudinary.config(
    cloud_name = "dyjzrfowo",
    api_key = "521452815374687",
    api_secret = "-Lxjs6EoS1LwC64BkpD7cRyWizg"
)

# =========================
# BASE DE DATOS
# =========================
def get_db_connection():
    conn = sqlite3.connect("productos.db")
    conn.row_factory = sqlite3.Row
    return conn

# Crear tabla si no existe
with get_db_connection() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            precio REAL NOT NULL,
            imagen TEXT NOT NULL
        )
    """)
    conn.commit()

# =========================
# RUTAS
# =========================

# Página principal (clientes)
@app.route("/")
def index():
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template("index.html", productos=productos)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        if usuario == "hosanna" and password == "18.2025":
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            flash("Usuario o contraseña incorrectos")
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Panel de administración
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template("admin.html", productos=productos)

# Subir producto CON CLOUDINARY
@app.route("/add", methods=["POST"])
def add():
    if not session.get("admin"):
        return redirect(url_for("login"))

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    imagen = request.files["imagen"]

    if imagen:
        try:
            # 🔥 SUBIR IMAGEN A CLOUDINARY
            upload_result = cloudinary.uploader.upload(
                imagen,
                folder="hosanna_productos",  # Carpeta en Cloudinary
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},  # Optimización
                    {'quality': 'auto', 'fetch_format': 'auto'}
                ]
            )
            
            # Obtener URL de la imagen subida
            imagen_url = upload_result['secure_url']
            
            # Guardar en base de datos
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO productos (nombre, descripcion, precio, imagen) VALUES (?, ?, ?, ?)",
                (nombre, descripcion, precio, imagen_url)
            )
            conn.commit()
            conn.close()
            
            flash("¡Producto agregado exitosamente!", "success")
            
        except Exception as e:
            flash(f"Error al subir imagen: {str(e)}", "error")
            return redirect(url_for("admin"))

    return redirect(url_for("admin"))

# Eliminar producto
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if not session.get("admin"):
        return redirect(url_for("login"))

    conn = get_db_connection()
    producto = conn.execute("SELECT * FROM productos WHERE id = ?", (id,)).fetchone()
    
    if producto:
        # Opcional: Eliminar imagen de Cloudinary
        # Para esto necesitarías guardar el public_id de la imagen
        # Por ahora solo eliminamos de la BD
        
        conn.execute("DELETE FROM productos WHERE id = ?", (id,))
        conn.commit()
        flash("Producto eliminado correctamente", "success")
    
    conn.close()
    return redirect(url_for("admin"))

# Editar producto (NUEVA FUNCIONALIDAD)
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    conn = get_db_connection()
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        imagen = request.files.get("imagen")
        
        if imagen and imagen.filename:
            # Subir nueva imagen a Cloudinary
            try:
                upload_result = cloudinary.uploader.upload(
                    imagen,
                    folder="hosanna_productos",
                    transformation=[
                        {'width': 800, 'height': 800, 'crop': 'limit'},
                        {'quality': 'auto', 'fetch_format': 'auto'}
                    ]
                )
                imagen_url = upload_result['secure_url']
                
                # Actualizar con nueva imagen
                conn.execute(
                    "UPDATE productos SET nombre=?, descripcion=?, precio=?, imagen=? WHERE id=?",
                    (nombre, descripcion, precio, imagen_url, id)
                )
            except Exception as e:
                flash(f"Error al actualizar imagen: {str(e)}", "error")
        else:
            # Actualizar sin cambiar imagen
            conn.execute(
                "UPDATE productos SET nombre=?, descripcion=?, precio=? WHERE id=?",
                (nombre, descripcion, precio, id)
            )
        
        conn.commit()
        conn.close()
        flash("Producto actualizado exitosamente", "success")
        return redirect(url_for("admin"))
    
    # GET: Mostrar formulario de edición
    producto = conn.execute("SELECT * FROM productos WHERE id = ?", (id,)).fetchone()
    conn.close()
    
    if not producto:
        flash("Producto no encontrado", "error")
        return redirect(url_for("admin"))
    
    return render_template("edit.html", producto=producto)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)