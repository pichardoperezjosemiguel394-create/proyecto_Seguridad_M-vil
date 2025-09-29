from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

# Inicializamos la aplicación Flask
app = Flask(__name__)
app.secret_key = '09f78ead-8a13-11f0-9f04-089798bc6dda'  # Clave secreta para la sesión

# ----------------- CONEXIÓN A MYSQL -----------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ventas'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)  # Inicializamos MySQL con la app

# ----------------- RUTAS -----------------

@app.route('/')
def inicio():
    return render_template("index.html")

@app.route('/contacto', methods=['GET', 'POST'])
def contacto():
    user = {'nombre': '', 'email': '', 'mensaje': ''}
    if request.method == 'GET':
        user['nombre'] = request.args.get('nombre', '')
        user['email'] = request.args.get('email', '')
        user['mensaje'] = request.args.get('mensaje', '')
    return render_template("contacto.html", usuario=user)

@app.route('/contactopost', methods=['GET', 'POST'])
def contactopost():
    user = {'nombre': '', 'email': '', 'mensaje': ''}
    if request.method == 'POST':
        user['nombre'] = request.form.get('nombre', '')
        user['email'] = request.form.get('email', '')
        user['mensaje'] = request.form.get('mensaje', '')
    return render_template("contactopost.html", usuario=user)

# ----------------- LOGIN -----------------
@app.route('/login', methods=['GET'])
def login():
    return render_template("login.html")

@app.route('/accesologin', methods=['POST'])
def accesologin():
    email = request.form.get('email')
    password = request.form.get('password')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuario WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()

    if user:
        session['usuario'] = user['email']
        session['nombre'] = user['nombre']
        session['rol'] = user['id_rol']

        if user['id_rol'] == 1:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('inicio'))
    else:
        flash('Usuario y Contraseña incorrecta','error')
        return redirect("login")

# ----------------- REGISTRO -----------------
@app.route('/Registro', methods=['GET', 'POST'])
def Registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        id_rol = 2  # Rol usuario por defecto

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuario (email, nombre, password, id_rol) VALUES (%s, %s, %s, %s)",
                    (email, nombre, password, id_rol))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('inicio'))

    return render_template("Registro.html")

# ----------------- PÁGINA DE USUARIO -----------------
@app.route('/usuario')
def usuario():
    if 'usuario' in session:
        return render_template("usuario.html", usuario=session['usuario'])
    else:
        return redirect(url_for('login'))
    
    

# -----------------  # RUTA DEL ADMIN # -----------------
@app.route('/admin')
def admin():
    if 'usuario' in session and session.get('rol') == 1:
        return render_template("admin.html", usuario=session['usuario'])
    else:
        flash('Usuario y Contraseña incorrecta', 'error')
        return redirect(url_for('login'))
    
    
    

#  ----------------- PERFIL DE USUARIO # -----------------
@app.route('/listar', methods=['GET', 'POST'])
def listar():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    # ----------------- AGREGAR USUARIO -----------------
    if request.method == 'POST' and 'agregar_usuario' in request.form:
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']
        id_rol = 2  # Rol por defecto

        cur.execute("INSERT INTO usuario (nombre, email, password, id_rol) VALUES (%s, %s, %s, %s)",
                    (nombre, email, password, id_rol))
        mysql.connection.commit()
        cur.close()
        flash("Usuario agregado correctamente!", "success")
        return redirect(url_for('listar'))  # <-- redirige después del POST

    # ----------------- EDITAR USUARIO -----------------
    elif request.method == 'POST' and 'editar_usuario' in request.form:
        user_id = request.form['id']
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        cur.execute("UPDATE usuario SET nombre=%s, email=%s, password=%s WHERE id=%s",
                    (nombre, email, password, user_id))
        mysql.connection.commit()
        cur.close()
        flash("Usuario actualizado correctamente!", "success")
        return redirect(url_for('listar'))  # <-- redirige después del POST

    # ----------------- ELIMINAR USUARIO -----------------
    if request.args.get('eliminar_usuario'):
        user_id = request.args.get('eliminar_usuario')
        cur.execute("DELETE FROM usuario WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()
        flash("Usuario eliminado correctamente!", "danger")
        return redirect(url_for('listar'))  # <-- redirige después de eliminar

    # ----------------- OBTENER USUARIOS -----------------
    cur.execute("SELECT * FROM usuario")
    usuarios = cur.fetchall()
    cur.close()

    return render_template("editar_usuario.html",
                           usuario=session['usuario'],
                           usuarios=usuarios)


# ----------------- PERFIL DE USUARIO-----------------





# ----------------- Registrar Productos # -----------------

import MySQLdb.cursors

@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        descripcion = request.form['descripcion']

        # Insertar en MySQL
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, precio, descripcion)
            VALUES (%s, %s, %s)
        """, (nombre, precio, descripcion))
        mysql.connection.commit()
        cur.close()

        flash('Curso agregado correctamente!', 'success')
        return redirect(url_for('agregar_producto'))

    # Obtener productos para mostrar en la tabla (DictCursor)
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()

    return render_template('Agregar_productos.html', productos=productos)


    

@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    flash('Producto eliminado correctamente!')
    return redirect(url_for('listar_productos_agregados'))

@app.route('/listar_productos_agregados')
def listar_productos_agregados():
    productos = []  # Temporalmente vacío
    return render_template('Agregar_productos.html', productos=productos)




# ----------------- LISTAR TODOS LOS PRODUCTOS -----------------
@app.route('/listar_productos')
def listar_productos():
    if 'usuario' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM productos ORDER BY id DESC")
        productos = cur.fetchall()
        cur.close()
        return render_template("listar_productos.html", usuario=session['usuario'], productos=productos)
    else:
        return redirect(url_for('login'))

# ----------------- RUTA PARA EDITAR PRODUCTO -----------------
@app.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    cur = mysql.connection.cursor()
    # Obtener el producto por ID para validar que exista
    cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
    producto = cur.fetchone()

    if not producto:
        flash("Producto no encontrado", "warning")
        cur.close()
        return redirect(url_for('listar_productos'))

    # Revisar si la acción es eliminar
    accion = request.form.get('accion')
    if accion == 'eliminar':
        cur.execute("DELETE FROM productos WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Producto eliminado correctamente!", "success")
        return redirect(url_for('listar_productos'))

    # Si no es eliminar, se asume que es actualizar
    nombre = request.form['nombre']
    precio = float(request.form['precio'])
    descripcion = request.form['descripcion']

    # Actualizar producto en la base de datos
    cur.execute("""
        UPDATE productos
        SET nombre=%s, precio=%s, descripcion=%s
        WHERE id=%s
    """, (nombre, precio, descripcion, id))
    mysql.connection.commit()
    cur.close()

    flash("Producto actualizado correctamente!", "success")
    return redirect(url_for('listar_productos'))




# ----------------- Registrar Productos # -----------------

# ----------------- ACERCA DE -----------------
@app.route('/acercade')
def acercade():
    return render_template("acercade.html")

# ----------------- LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

# ----------------- MAIN -----------------
if __name__ == '__main__':
    app.run(debug=True, port=8000)
