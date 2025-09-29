from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
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
cloudinary.config(
    cloud_name = "dyjzrfowo",
    api_key = "521452815374687",
    api_secret = "-Lxjs6EoS1LwC64BkpD7cRyWizg"
)

# =========================
# MIDDLEWARE DE PROTECCIÓN
# =========================
def login_required(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            flash("Debes iniciar sesión para acceder a esta página", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

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
    # Si ya está autenticado, redirigir al admin
    if session.get("admin"):
        return redirect(url_for("admin"))
    
    if request.method == "POST":
        usuario = request.form["usuario"]
        password = request.form["password"]
        if usuario == "hosanna" and password == "18.2025":
            session["admin"] = True
            flash("¡Bienvenida al panel de administración!", "success")
            return redirect(url_for("admin"))
        else:
            flash("Usuario o contraseña incorrectos", "error")
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for("index"))

# Panel de administración - AHORA PROTEGIDO
@app.route("/admin")
@login_required
def admin():
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM productos").fetchall()
    conn.close()
    return render_template("admin.html", productos=productos)

# Subir producto - PROTEGIDO
@app.route("/add", methods=["POST"])
@login_required
def add():
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    imagen = request.files["imagen"]

    if imagen:
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

# Eliminar producto - PROTEGIDO
@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    conn = get_db_connection()
    producto = conn.execute("SELECT * FROM productos WHERE id = ?", (id,)).fetchone()
    
    if producto:
        conn.execute("DELETE FROM productos WHERE id = ?", (id,))
        conn.commit()
        flash("Producto eliminado correctamente", "success")
    
    conn.close()
    return redirect(url_for("admin"))

# Editar producto - PROTEGIDO
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    conn = get_db_connection()
    
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        precio = request.form["precio"]
        imagen = request.files.get("imagen")
        
        if imagen and imagen.filename:
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
                
                conn.execute(
                    "UPDATE productos SET nombre=?, descripcion=?, precio=?, imagen=? WHERE id=?",
                    (nombre, descripcion, precio, imagen_url, id)
                )
            except Exception as e:
                flash(f"Error al actualizar imagen: {str(e)}", "error")
        else:
            conn.execute(
                "UPDATE productos SET nombre=?, descripcion=?, precio=? WHERE id=?",
                (nombre, descripcion, precio, id)
            )
        
        conn.commit()
        conn.close()
        flash("Producto actualizado exitosamente", "success")
        return redirect(url_for("admin"))
    
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