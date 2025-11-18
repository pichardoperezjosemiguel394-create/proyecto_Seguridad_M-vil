from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import os
import time
from werkzeug.utils import secure_filename
import bcrypt
import hashlib
from datetime import datetime

# Inicializamos la aplicación Flask
app = Flask(__name__, template_folder="Templates", static_folder="Static")
app.secret_key = '09f78ead-8a13-11f0-9f04-089798bc6dda'

# ----------------- CONEXIÓN A MYSQL CLEVER CLOUD mmmm-----------------
app.config['MYSQL_HOST'] = 'btmfogckn3sqq1kqc0r0-mysql.services.clever-cloud.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'u9cseiqaxtklybvx'
app.config['MYSQL_PASSWORD'] = '0nMxe8SZ3ZostJgVW2ag'
app.config['MYSQL_DB'] = 'btmfogckn3sqq1kqc0r0'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Configuración para uploads de imágenes
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

mysql = MySQL(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------- FUNCIONES DE ENCRIPTACIÓN DE contrase;a -----------------
def encriptar_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verificar_password(password_plana, password_encriptada):
    if password_plana == password_encriptada:
        return True
    elif len(password_encriptada) == 64:
        hash_ingresado = hashlib.sha256(password_plana.encode('utf-8')).hexdigest()
        return hash_ingresado == password_encriptada
    elif password_encriptada.startswith('$2b$'):
        try:
            return bcrypt.checkpw(password_plana.encode('utf-8'), password_encriptada.encode('utf-8'))
        except:
            return False
    else:
        return False

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
    cur.execute("SELECT * FROM usuario WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and verificar_password(password, user['password']):
        session['usuario'] = user['email']
        session['nombre'] = user['nombre']
        session['rol'] = user['id_rol']
        session['id'] = user['id']
        session['email'] = user['email']

        if user.get('foto_perfil'):
            session['foto_perfil'] = user['foto_perfil']
        else:
            session['foto_perfil'] = 'img/user.png'

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
        id_rol = 2

        password_encriptada = encriptar_password(password)

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuario (email, nombre, password, id_rol) VALUES (%s, %s, %s, %s)",
                    (email, nombre, password_encriptada, id_rol))
        mysql.connection.commit()
        cur.close()

        flash('Usuario registrado correctamente!', 'success')
        return redirect(url_for('inicio'))

    return render_template("Registro.html")

# ----------------- PÁGINA DE USUARIO -----------------
@app.route('/usuario')
def usuario():
    if 'usuario' in session:
        return render_template("usuario.html", usuario=session['usuario'])
    else:
        return redirect(url_for('login'))

# ----------------- RUTA DEL ADMIN -----------------
@app.route('/admin')
def admin():
    if 'usuario' in session and session.get('rol') == 1:
        return render_template("admin.html", usuario=session['usuario'])
    else:
        flash('Usuario y Contraseña incorrecta', 'error')
        return redirect(url_for('login'))

# ----------------- PERFIL DE USUARIO -----------------
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
        id_rol = 2

        password_encriptada = encriptar_password(password)

        cur.execute("INSERT INTO usuario (nombre, email, password, id_rol) VALUES (%s, %s, %s, %s)",
                    (nombre, email, password_encriptada, id_rol))
        mysql.connection.commit()
        cur.close()
        flash("Usuario agregado correctamente!", "success")
        return redirect(url_for('listar'))

    # ----------------- EDITAR USUARIO -----------------
    elif request.method == 'POST' and 'editar_usuario' in request.form:
        user_id = request.form['id']
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        if password and not password.startswith('$2b$') and len(password) != 64:
            password_encriptada = encriptar_password(password)
            cur.execute("UPDATE usuario SET nombre=%s, email=%s, password=%s WHERE id=%s",
                        (nombre, email, password_encriptada, user_id))
        else:
            cur.execute("UPDATE usuario SET nombre=%s, email=%s WHERE id=%s",
                        (nombre, email, user_id))
        
        mysql.connection.commit()
        cur.close()
        flash("Usuario actualizado correctamente!", "success")
        return redirect(url_for('listar'))

    # ----------------- ELIMINAR USUARIO -----------------
    if request.args.get('eliminar_usuario'):
        user_id = request.args.get('eliminar_usuario')
        cur.execute("DELETE FROM usuario WHERE id = %s", (user_id,))
        mysql.connection.commit()
        cur.close()
        flash("Usuario eliminado correctamente!", "danger")
        return redirect(url_for('listar'))

    # ----------------- OBTENER USUARIOS -----------------
    cur.execute("SELECT * FROM usuario")
    usuarios = cur.fetchall()
    cur.close()

    # CONVERTIR FECHAS - CORRECCIÓN: usar fecha_creacion y fecha_actualizacion
    for usuario in usuarios:
        if 'fecha_creacion' in usuario and usuario['fecha_creacion']:
            try:
                usuario['fecha_creacion'] = datetime.strptime(str(usuario['fecha_creacion']), '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Error convirtiendo fecha_creacion: {e}")
                pass
        
        if 'fecha_actualizacion' in usuario and usuario['fecha_actualizacion']:
            try:
                usuario['fecha_actualizacion'] = datetime.strptime(str(usuario['fecha_actualizacion']), '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                print(f"Error convirtiendo fecha_actualizacion: {e}")
                pass

    return render_template("editar_usuario.html",
                           usuario=session['usuario'],
                           usuarios=usuarios)

# ----------------- RUTAS PARA EL PERFIL -----------------

@app.route('/cambiar_foto_perfil', methods=['POST'])
def cambiar_foto_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        foto_predefinida = request.form.get('foto_predefinida')
        if foto_predefinida:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE usuario SET foto_perfil = %s WHERE id = %s", 
                       (foto_predefinida, session['id']))
            mysql.connection.commit()
            session['foto_perfil'] = foto_predefinida
            cur.close()
            flash('Foto de perfil actualizada correctamente', 'success')
            return redirect(url_for('listar'))
        
        file = request.files.get('foto')
        if file and file.filename:
            if allowed_file(file.filename):
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"user_{session['id']}_{int(time.time())}.{file_extension}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                file.save(filepath)
                
                db_filepath = f"img/{unique_filename}"
                
                cur = mysql.connection.cursor()
                cur.execute("UPDATE usuario SET foto_perfil = %s WHERE id = %s", 
                           (db_filepath, session['id']))
                mysql.connection.commit()
                cur.close()
                
                session['foto_perfil'] = db_filepath
                flash('Foto de perfil actualizada correctamente', 'success')
            else:
                flash('Formato de archivo no permitido. Use: PNG, JPG, JPEG, GIF', 'error')
        else:
            flash('No se seleccionó ningún archivo', 'error')
            
    except Exception as e:
        flash(f'Error al actualizar la foto: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        nombre = request.form['nombre']
        email = request.form['email']
        
        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuario SET nombre = %s, email = %s WHERE id = %s", 
                   (nombre, email, session['id']))
        mysql.connection.commit()
        
        session['nombre'] = nombre
        session['email'] = email
        session['usuario'] = email
        
        flash('Perfil actualizado correctamente', 'success')
        cur.close()
        
    except Exception as e:
        flash(f'Error al actualizar el perfil: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

@app.route('/cambiar_password', methods=['POST'])
def cambiar_password():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        password_actual = request.form['password_actual']
        nueva_password = request.form['nueva_password']
        confirmar_password = request.form['confirmar_password']
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM usuario WHERE id = %s", (session['id'],))
        usuario = cur.fetchone()
        
        if usuario and verificar_password(password_actual, usuario['password']):
            if nueva_password == confirmar_password:
                nueva_password_encriptada = encriptar_password(nueva_password)
                
                cur.execute("UPDATE usuario SET password = %s WHERE id = %s", 
                           (nueva_password_encriptada, session['id']))
                mysql.connection.commit()
                flash('Contraseña actualizada correctamente', 'success')
            else:
                flash('Las contraseñas nuevas no coinciden', 'error')
        else:
            flash('Contraseña actual incorrecta', 'error')
        
        cur.close()
        
    except Exception as e:
        flash(f'Error al cambiar la contraseña: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

# ----------------- PRODUCTOS -----------------

@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = float(request.form['precio'])
        descripcion = request.form['descripcion']

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO productos (nombre, precio, descripcion)
            VALUES (%s, %s, %s)
        """, (nombre, precio, descripcion))
        mysql.connection.commit()
        cur.close()

        flash('Técnica agregada correctamente!', 'success')
        return redirect(url_for('agregar_producto'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()

    return render_template('Agregar_productos.html', productos=productos)

@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Técnica eliminada correctamente!', 'success')
    return redirect(url_for('listar_productos'))

@app.route('/listar_productos_agregados')
def listar_productos_agregados():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()
    
    return render_template('Agregar_productos.html', productos=productos)

@app.route('/listar_productos')
def listar_productos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos ORDER BY id DESC")
    productos = cur.fetchall()
    cur.close()
    
    return render_template("listar_productos.html", 
                         usuario=session['usuario'], 
                         productos=productos)

@app.route('/editar_producto/<int:id>', methods=['POST'])
def editar_producto(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    
    accion = request.form.get('accion')
    if accion == 'eliminar':
        cur.execute("DELETE FROM productos WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash("Técnica eliminada correctamente!", "success")
        return redirect(url_for('listar_productos'))

    nombre = request.form['nombre']
    precio = float(request.form['precio'])
    descripcion = request.form['descripcion']

    cur.execute("""
        UPDATE productos
        SET nombre=%s, precio=%s, descripcion=%s
        WHERE id=%s
    """, (nombre, precio, descripcion, id))
    mysql.connection.commit()
    cur.close()

    flash("Técnica actualizada correctamente!", "success")
    return redirect(url_for('listar_productos'))

@app.route('/encriptar_contraseñas', methods=['POST'])
def encriptar_contraseñas():
    if 'usuario' not in session or session.get('rol') != 1:
        flash('No tienes permisos para esta acción', 'error')
        return redirect(url_for('login'))
    
    try:
        cur = mysql.connection.cursor()
        
        cur.execute("SELECT id, password FROM usuario")
        usuarios = cur.fetchall()
        
        usuarios_actualizados = 0
        
        for usuario in usuarios:
            password_actual = usuario['password']
            
            if not password_actual.startswith('$2b$'):
                password_encriptada = encriptar_password("1234")
                
                cur.execute("UPDATE usuario SET password = %s WHERE id = %s", 
                           (password_encriptada, usuario['id']))
                usuarios_actualizados += 1
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'Se encriptaron {usuarios_actualizados} contraseñas correctamente. Todas las contraseñas ahora son: 1234', 'success')
        
    except Exception as e:
        flash(f'Error al encriptar contraseñas: {str(e)}', 'error')
    
    return redirect(url_for('listar'))

@app.route('/acercade')
def acercade():
    return render_template("acercade.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)