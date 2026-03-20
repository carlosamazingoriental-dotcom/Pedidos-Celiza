from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"  # Cambiar por algo seguro

def get_db():
    conn = sqlite3.connect("pedidos.db")
    conn.row_factory = sqlite3.Row
    return conn

# ========================
# LOGIN
# ========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        user = db.execute(
            "SELECT * FROM usuarios WHERE username=? AND password=?", 
            (username, password)
        ).fetchone()
        db.close()
        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect("/pedidos")
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
    return render_template("login.html", error=None)

# ========================
# PEDIDOS
# ========================
@app.route("/pedidos", methods=["GET", "POST"])
def pedidos():
    if "username" not in session:
        return redirect("/")

    db = get_db()
    user = session["username"]
    role = session["role"]

    # Crear nuevo pedido
    if request.method == "POST":
        detalles = request.form["detalles"]
        fecha_pedido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Si es admin, tomar el usuario seleccionado, si no, usar el propio
        pedido_usuario = request.form.get("pedido_usuario") if role=="admin" else user
        db.execute(
            "INSERT INTO pedidos (detalles, usuario, fecha_pedido) VALUES (?, ?, ?)",
            (detalles, pedido_usuario, fecha_pedido)
        )
        db.commit()
        db.close()
        # REDIRECT para evitar duplicados al refrescar
        return redirect("/pedidos")

    # Consultar pedidos
    if role == "admin":
        pedidos_list = db.execute("SELECT * FROM pedidos").fetchall()
    else:
        pedidos_list = db.execute("SELECT * FROM pedidos WHERE usuario=?", (user,)).fetchall()

    db.close()
    return render_template("pedidos.html", pedidos=pedidos_list, user=user, role=role)

# ========================
# MARCAR TRAMITADO (solo admin)
# ========================
@app.route("/tramitado/<int:id>")
def tramitado(id):
    if "username" not in session or session["role"] != "admin":
        return "No tienes permiso para tramitar este pedido", 403

    db = get_db()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        "UPDATE pedidos SET estado='tramitado', fecha_tramitado=? WHERE id=?",
        (fecha_actual, id)
    )
    db.commit()
    db.close()
    return redirect("/pedidos")

# ========================
# CERRAR SESIÓN
# ========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ========================
# EJECUTAR APP
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)