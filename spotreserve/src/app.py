from flask import Flask, session, render_template, request, redirect, url_for
from flask_mail import Mail, Message
from flask_socketio import SocketIO, emit
from flask import redirect, url_for, flash
from flask_talisman import Talisman
import random
import re
import datetime
import sqlite3

app = Flask(__name__, template_folder='template')
app.secret_key = "pinchellave"
# Database configuration
DATABASE = 'flask_login.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'spotreserve2@gmail.com'
app.config['MAIL_PASSWORD'] = 'vepr gkzt cidc xfow'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Activations
mail = Mail(app)
socketio = SocketIO(app)

#____________________________________________________CONEXIONES_______________________________________________________

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return redirect(url_for('listar_usuarios'))


@app.route('/admin2')
def admin2():
    return redirect(url_for('listar_usuarios2'))

@app.route('/reserva')
def reserva():
    return render_template('reserva.html')

@app.route('/baresvip')
def baresvip():
    return render_template('baresvip.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registro_bar')
def registrobar():
    return render_template('registro_propietarios.html')

#____________________________________________________Iniciar o cerrar sesion__________________________________________
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# Función para verificar si el usuario está logueado
def verificar_login():
    if 'logueado' not in session:
        return redirect(url_for('login'))

@app.before_request
def check_access():
    if request.endpoint in ['admin', 'listar_usuarios'] and not ('logueado' in session and session.get('id_rol') == 1):
        return redirect(url_for('login'))

@app.route('/login')
def show_login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logueado', None)
    session.pop('username', None)
    session.pop('id_rol', None)
    return redirect(url_for('login'))

@app.route('/login', methods=["POST"])
def iniciarOcerrar():
    mensaje = None
    if 'txtUsername' in request.form and 'txtPassword' in request.form:
        _username = request.form['txtUsername']
        _password = request.form['txtPassword']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM user WHERE username = ? AND password = ?', (_username, _password,))
        account = cur.fetchone()

        if account:
            session['logueado'] = True
            session['id'] = account['id']
            session['id_rol'] = account['id_rol']

            if session['id_rol'] == 1:
                return redirect(url_for('admin'))
            elif session['id_rol'] == 2:
                return redirect(url_for('admin2'))
        else:
            cur.execute('SELECT * FROM user WHERE username = ?', (_username,))
            user = cur.fetchone()
            if user:
                mensaje = "Contraseña incorrecta"
            else:
                mensaje = "Usuario no registrado"

        cur.close()
        conn.close()

    return render_template("login.html", mensaje=mensaje)

#___________________________________________________INCICIO O CIERRE DE SESION___________________________________________________

def verificar_login():
    if 'logueado' not in session:
        return redirect(url_for('login'))
    
@app.before_request
def check_access():
    if request.endpoint == 'reserva' and not session.get('logueado'):
        return redirect(url_for('login'))

@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    mensaje = None
    if request.method == 'POST' and 'txtUsername' in request.form and 'txtPassword' in request.form:
        _username = request.form['txtUsername']
        _password = request.form['txtPassword']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM user WHERE username = ? AND password = ?', (_username, _password,))
        account = cur.fetchone()
      
        if account:
            session['logueado'] = True
            session['id'] = account['id']
            session['id_rol'] = account['id_rol']

            if session['id_rol'] == 1:
                return redirect(url_for('admin'))
            elif session['id_rol'] == 2:
                return redirect(url_for('admin2'))
        else:
            cur.execute('SELECT * FROM user WHERE username = ?', (_username,))
            user = cur.fetchone()
            if user:
                mensaje = "Contraseña incorrecta"
            else:
                mensaje = "Usuario no registrado "

        cur.close()
        conn.close()
        
    return render_template("login.html", mensaje=mensaje)

@app.route('/inicio_sesion', methods=['GET', 'POST'])
def inicio_sesion():
    if request.method == 'POST':
        # Obtener los datos del formulario
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']

        # Verificar las credenciales del usuario
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, id_rol FROM registro_propietarios WHERE usuario = ? AND contraseña = ?", (usuario, contraseña))
        user = cur.fetchone()
        cur.close()

        if user:
            session['logueado'] = True
            session['id'] = user['id']
            session['id_rol'] = user['id_rol']
            session['username'] = usuario
            conn.close()
            return redirect(url_for('listar_reservas'))  # Cambiar referencia aquí
        else:
            # Manejar error de inicio de sesión
            conn.close()
            return "Usuario o contraseña incorrectos"
    return render_template('login.html')



#__________________________________________________REGISTROS_________________________________________________________-

# Register user
@app.route('/crear-registro', methods=["POST"])
def crear_registro():
    # Obtener los datos del formulario
    _firstname = request.form['txtFirstName']
    _lastname = request.form['txtLastName']
    username = request.form['txtUsername']
    password = request.form['txtPassword']
    _txtemail = request.form['txtEmail']
    _txtaddress = request.form['txtAddress']
    _fileupload = request.form['fileUpload']

    fullname = f"{_firstname} {_lastname}"

    mensaje_correo = None
    mensaje_contrasena = None

    if not re.match(r"[^@]+@[^@]+\.[^@]+", _txtemail):
        mensaje_correo = "Por favor, ingrese un correo electrónico válido."

    if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password) or not any(char in "!@#$%^&*()-+" for char in password):
        mensaje_contrasena = "La contraseña debe tener al menos 8 caracteres, incluir al menos una mayúscula, un número y un carácter especial (!@#$%^&*()-+)."

    verification_code = generate_verification_code()
    send_verification_email(_txtemail, verification_code)

    session['verification_code'] = verification_code
    session['pending_user'] = {
        'firstname': _firstname,
        'lastname': _lastname,
        'username': username,
        'password': password,
        'email': _txtemail,
        'address': _txtaddress,
        'fileupload': _fileupload,
        'fullname': fullname
    }

    return redirect(url_for('verificar'))

@app.route('/verificar', methods=["GET", "POST"])
def verificar():
    mensaje = None
    if request.method == 'POST':
        user_code = request.form['verification_code']
        if user_code == session.get('verification_code'):
            pending_user = session.get('pending_user')
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO registro_clientes (firstname, lastname, username, password, id_rol, email, address, fileupload) VALUES (?, ?, ?, ?, '2', ?, ?, ?)",
                        (pending_user['firstname'], pending_user['lastname'], pending_user['username'], pending_user['password'], pending_user['email'], pending_user['address'], pending_user['fileupload']))
            conn.commit()
            cur.execute("INSERT INTO user (username, password, id_rol, fullname) VALUES (?, ?, '2', '')",
                        (pending_user['username'], pending_user['password']))
            conn.commit()
            conn.close()
            return render_template('login.html', mensaje2="Usuario registrado correctamente")
        else:
            mensaje = "Código de verificación incorrecto. Por favor, inténtelo de nuevo."
    
    return render_template('verificacion.html', mensaje=mensaje, email=session.get('pending_user')['email'])


@app.route('/reenviar-codigo')
def reenviar_codigo():
    verification_code = generate_verification_code()
    send_verification_email(session['pending_user']['email'], verification_code)
    session['verification_code'] = verification_code
    return redirect(url_for('verificar'))

# Register bar
@app.route('/send_verification_code', methods=["POST"])
def send_verification_code():
    # Get data from the form
    _firstnameb = request.form['txtbFirstName']
    _lastnameb = request.form['txtbLastName']
    username = request.form['txtbUsername']
    password = request.form['txtbPassword']
    _txtlocal = request.form['txtUblocal']
    _txtemailb = request.form['txtbEmail']
    _txtaddressb = request.form['txtbAddress']
    _fileuploadb = request.form['filebUpload']
    
    # Generate verification code
    verification_code = generar_codigo_verificacion()
    
    # Send verification code to user's email
    enviar_correo_verificacion(_txtemailb, verification_code)
    
    # Store user data and verification code in session
    session['user_data'] = {
        'firstname': _firstnameb,
        'lastname': _lastnameb,
        'username': username,
        'password': password,
        'local': _txtlocal,
        'email': _txtemailb,
        'address': _txtaddressb,
        'image': _fileuploadb
    }
    session['verification_code'] = verification_code
    
    return render_template('verify_code.html')

@app.route('/verify_code', methods=["POST"])
def verify_code():
    # Get the verification code from the form
    entered_code = request.form['verification_code']
    
    # Check if the entered code matches the generated code
    if entered_code == session.get('verification_code'):
        # Get user data from session
        user_data = session.get('user_data')
        
        # Create a cursor to interact with the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Execute an SQL query to insert the data into the table
        cur.execute("INSERT INTO registro_propietarios (nombre, apellido, usuario, contraseña, nombreLocal, email, direccion, imagen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                    (user_data['firstname'], user_data['lastname'], user_data['username'], user_data['password'], user_data['local'], user_data['email'], user_data['address'], user_data['image']))
        conn.commit() 
        cur.execute("INSERT INTO user (username, password, id_rol, fullname) VALUES (?, ?, '1', '')", 
                        (user_data['username'], user_data['password']))
        conn.commit()

        cur.close()
        conn.close()
        # Clear session data
        session.pop('user_data', None)
        session.pop('verification_code', None)
        
        return render_template('login.html', mensaje2="Propietario registrado correctamente")
    else:
        mensaje = "Código de verificación incorrecto. Por favor, inténtelo de nuevo."
    return render_template('verify_code.html', mensaje=mensaje)


@app.route('/reenviar-codigo-bar')
def reenviar_codigo_bar():
    verification_code = generate_verification_code()
    send_verification_email(session['pending_bar']['email'], verification_code)
    session['verification_code'] = verification_code
    return redirect(url_for('verificar_bar'))

#______________________________________________FUNCIONALIDADES DE EMAIL________________________________________________
def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_email(email, code):
    msg = Message('Código de Verificación', sender='tomasalejandro442@gmail.com', recipients=[email])
    msg.body = f'Su código de verificación es {code}.'
    mail.send(msg)

def generar_codigo_verificacion():
    return str(random.randint(100000, 999999))

def enviar_correo_verificacion(email, codigo):
    msg = Message('Código de Verificación', sender='spotreserve2@gmail.com', recipients=[email])
    msg.body = f'Su código de verificación es {codigo}.'
    mail.send(msg)

#__________________________________________Enviar las listas de los usuarios____________________________________________

@app.route('/listar', methods=["GET", "POST"])
def listar_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reserva")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("admin.html", usuarios=usuarios, username=session.get('username'))

@app.route('/api/reservas', methods=["GET"])
def obtener_reservas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM reserva")
    reservas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(ix) for ix in reservas])

@app.route('/reservasUsuarios', methods=["GET", "POST"])
def listar_usuarios2():
    if 'logueado' in session:
        user_id = session['id']  # Obtener el ID del usuario de la sesión
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM reserva WHERE id_usuario = ?", (user_id,))
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        return render_template("admin2.html", usuarios=usuarios, username=session.get('username'))
    else:
        return redirect(url_for('login'))

#__________________________________________FUNCIONALIDADES DE RESERVA_____________________________________________________

@app.route('/reservar', methods=['POST'])
def reservar():
    if request.method == 'POST':
        # Obtener el ID del usuario de la sesión
        user_id = session.get('id')

        # Obtener otros datos del formulario
        restaurante = request.form['nombreLocal']
        nombre = request.form['nombre']
        cantidad_personas = request.form['cantidad_personas']
        fecha_reserva = request.form['fecha_reserva']
        hora_reserva = request.form['hora_reserva']
        comentarios = request.form['comentarios']

        # Buscar el correo electrónico del usuario en la tabla "registro_clientes" utilizando su ID
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT email FROM registro_clientes WHERE id = ?", (user_id,))
        usuario = cur.fetchone()

        if usuario:
            email_usuario = usuario['email']

            # Insertar la reserva en la base de datos
            cur.execute("INSERT INTO reserva (id_usuario, nombreLocal, nombre_cliente, cantidad_personas, fecha_reserva, hora_reserva, comentarios) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (user_id, restaurante, nombre, cantidad_personas, fecha_reserva, hora_reserva, comentarios))
            conn.commit()

            # Obtener la última reserva insertada para enviar a la gráfica
            cur.execute("SELECT * FROM reserva ORDER BY id_reserva DESC LIMIT 1")
            nueva_reserva = cur.fetchone()
            new_data = {
                'timestamp': nueva_reserva['fecha_reserva'] + 'T' + nueva_reserva['hora_reserva'],
                'value': int(nueva_reserva['cantidad_personas'])
            }
            socketio.emit('new_data', new_data)  # Uso correcto de socketio

            # Emitir un evento para actualizar la tabla en tiempo real
            reservas = [dict(ix) for ix in cur.execute("SELECT * FROM reserva").fetchall()]
            socketio.emit('update_table', reservas)

            cur.close()
            conn.close()

            # Enviar correo de confirmación de reserva
            enviar_correo_confirmacion_reserva(email_usuario)

            return render_template("enviar_notificacion.html")
        else:
            cur.close()
            conn.close()
            return "No se pudo encontrar el correo del usuario en la base de datos."

# Enviar correo de confirmación de reserva
def enviar_correo_confirmacion_reserva(email_usuario):
    msg = Message("Confirmación de Reserva", sender='spotreserve2@gmail.com', recipients=[email_usuario])
    msg.body = "Gracias por hacer por hacer una reserva, por favor dirigase a panel de resversa para confirmarla o cancelar su reserva"
    mail.send(msg)

@app.route('/obtener_bares', methods=["GET"])
def obtener_bares():
    # Inicializar una lista para almacenar los nombres de los bares
    nombres_bares = []

    # Conectar a la base de datos y obtener los nombres de los bares
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT nombreLocal FROM registro_propietarios")
    resultados = cur.fetchall()
    cur.close()
    conn.close()

    # Agregar los nombres de los bares a la lista
    for resultado in resultados:
        nombres_bares.append(resultado['nombreLocal'])

    # Renderizar la plantilla con los nombres de los bares
    return render_template("reserva.html", nombres_bares=nombres_bares)



#botones

#aceptar reserva
@app.route('/aceptar_reserva', methods=['POST'])
def aceptar_reserva():
    if 'logueado' not in session:
        return redirect(url_for('login'))

    nombreLocal = request.form['nombreLocal']
    user_id = request.form['user_id']

    # Consulta si el nombreLocal existe en la base de datos
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM registro_propietarios WHERE nombreLocal = ?", (nombreLocal,))
    local = cur.fetchone()

    if local:
        # Obtener el correo del usuario
        cur.execute("SELECT email FROM registro_clientes WHERE id = ?", (user_id,))
        usuario = cur.fetchone()

        if usuario:
            email_usuario = usuario['email']
            
            # Insertar la reserva en la base de datos (asegurarse de que esta función inserte la reserva)
            cur.execute("INSERT INTO reserva (id_usuario, nombreLocal, nombre_cliente, cantidad_personas, fecha_reserva, hora_reserva, comentarios) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (user_id, nombreLocal, request.form['nombre'], request.form['cantidad_personas'], request.form['fecha_reserva'], request.form['hora_reserva'], request.form['comentarios']))
            conn.commit()

            # Emitir un evento para actualizar la tabla y gráfica en tiempo real
            reservas = [dict(ix) for ix in cur.execute("SELECT * FROM reserva").fetchall()]
            socketio.emit('update_table', reservas)
            socketio.emit('new_data', {
                'timestamp': request.form['fecha_reserva'] + 'T' + request.form['hora_reserva'],
                'value': int(request.form['cantidad_personas'])
            })

            cur.close()
            conn.close()

            # Enviar el correo de confirmación
            enviar_correo_confirmacion_reserva(email_usuario)

            return redirect(url_for('listar_usuarios'))
        else:
            cur.close()
            conn.close()
            return "No se pudo encontrar el correo del usuario en la base de datos."
    else:
        cur.close()
        conn.close()

        # Si no existe, envía un correo de solicitud de reserva al administrador
        enviar_correo_confirmacion_reserva(nombreLocal)
        return "La reserva no se pudo realizar automáticamente. Se ha enviado una solicitud al administrador."

# Cancelar Reserva
@app.route('/cancelar_reserva/<int:id_reserva>', methods=['POST'])
def cancelar_reserva(id_reserva):
    # Verificar si el usuario está logueado
    if 'logueado' not in session:
        return redirect(url_for('login'))

    # Eliminar la reserva de la base de datos
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM reserva WHERE id_reserva = ?", (id_reserva,))
    conn.commit()

    # Emitir un evento para actualizar la tabla y gráfica en tiempo real
    reservas = [dict(ix) for ix in cur.execute("SELECT * FROM reserva").fetchall()]
    socketio.emit('update_table', reservas)
    socketio.emit('cancel_data', id_reserva)

    cur.close()
    conn.close()

    # Redirigir automáticamente a la página de reservas
    return redirect(url_for('listar_usuarios'))


def reservar():
    # Obtener el ID del usuario de la sesión
    user_id = session.get('id')

    # Obtener el correo electrónico del usuario de la tabla "registro_clientes" utilizando su ID
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT email FROM registro_clientes WHERE id = ?", (user_id,))
    usuario = cur.fetchone()
    cur.close()
    conn.close()
    
    if usuario:
        email_usuario = usuario['email']
        enviar_correo_confirmacion_reserva(email_usuario)
        return "Correo de confirmación enviado correctamente."
    else:
        return "No se pudo encontrar el correo del usuario."




# Enviar correo de confirmación de reserva
def enviar_correo_confirmacion_reserva(email_usuario):
    msg = Message("Confirmación de Reserva", sender='spotreserve2@gmail.com', recipients=[email_usuario])
    msg.body = "Su reserva ha sido confirmada con éxito. ¡Esperamos verte pronto!"
    mail.send(msg)


#_____________________________________________________Funcionalidades de bar & Mapa_______________________________________

@app.template_filter('b64encode')
def b64encode_filter(data):
    return base64.b64encode(data).decode('utf-8')

@app.route('/get_image/<int:image_id>', methods=["GET", "POST"])
def get_image(image_id):
    try:
        # Verificar si la conexión a la base de datos está disponible
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT fileUpload FROM registro_clientes WHERE id = ?", (image_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()

        if result and result['fileUpload']:
            img_data = result['fileUpload']
            print(f"Image data length for id {image_id}: {len(img_data)}")

            # Suponiendo que los datos de la imagen están codificados en base64
            # Si no lo están, ajusta esta parte según el formato real de tus datos de imagen
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            image_html = f'<img src="data:image/jpeg;base64,{img_base64}" alt="Image">'
            return render_template('show_image.html', image_html=image_html)
        else:
            return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        print(f"Error retrieving image id {image_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/show_image/<int:image_id>', methods=["GET", "POST"])
def show_image(image_id):
    return render_template('show_image.html', image_id=image_id)

@app.route('/bares')
def listar_bares():
    # Establecer la conexión con la base de datos
    conn = sqlite3.connect('flask_login.db')
    cur = conn.cursor()

    # Ejecutar la consulta para obtener los datos de los bares
    cur.execute("SELECT id, nombreLocal, imagen FROM registro_propietarios")
    bares = cur.fetchall()
    # Convertir los datos de los bares en una lista de diccionarios
    bares_con_diccionarios = []
    for bar in bares:
        bares_con_diccionarios.append({'id': bar[0], 'nombreLocal': bar[1], 'imagen': bar[2]})

    # Cerrar la conexión con la base de datos
    cur.close()
    conn.close()

    return render_template("bares.html", bares=bares_con_diccionarios)


@app.route('/mapa/<int:bar_id>')
def mostrar_mapa(bar_id):
    # Establecer la conexión con la base de datos
    conn = sqlite3.connect('flask_login.db')
    cur = conn.cursor()

    # Ejecutar la consulta para obtener los datos del bar con el ID proporcionado
    cur.execute("SELECT nombreLocal, direccion FROM registro_propietarios WHERE id = ?", (bar_id,))
    bar = cur.fetchone()

    # Cerrar la conexión con la base de datos
    cur.close()
    conn.close()

    if bar:
       return render_template("calcularMapa.html", bar=bar)
    else:
       return "Bar no encontrado", 404
#___________________________________________formulario de contactos______________________________________________________

@app.route('/contact')
def contact():
    return render_template('contact_form.html')

@app.route('/send_contact_email', methods=['POST'])
def send_contact_email():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        msg = Message('New Contact Form Submission',
                      sender='spotreserve2@gmail.com',
                      recipients=['spotreserve2@gmail.com'])
        msg.body = f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}'
        try:
            mail.send(msg)
            flash('Message sent successfully!', 'success')
        except Exception as e:
            print(str(e))
            flash('Failed to send message. Please try again later.', 'danger')

        return redirect(url_for('contact'))




#________________________________________________________MAIN_____________________________________________________________

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
