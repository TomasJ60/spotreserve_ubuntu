#!/usr/bin/python3
import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('flask_login.db')
print("Opened database successfully")

# Crear la tabla registro_clientes
conn.execute('''
CREATE TABLE registro_clientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  firstName VARCHAR(100) NOT NULL,
  lastName VARCHAR(100) NOT NULL,
  username VARCHAR(100) NOT NULL,
  password VARCHAR(100) NOT NULL,
  id_rol INTEGER NOT NULL,
  email VARCHAR(100) NOT NULL,
  address VARCHAR(100) NOT NULL,
  fileUpload BLOB NOT NULL
);
''')

print("Table registro_clientes created successfully")

# Crear la tabla registro_propietarios
conn.execute('''
CREATE TABLE registro_propietarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre VARCHAR(50) DEFAULT NULL,
  apellido VARCHAR(100) DEFAULT NULL,
  usuario VARCHAR(100) NOT NULL,
  contraseña VARCHAR(100) DEFAULT NULL,
  nombreLocal VARCHAR(100) NOT NULL,
  email VARCHAR(100) DEFAULT NULL,
  direccion VARCHAR(100) DEFAULT NULL,
  imagen BLOB DEFAULT NULL,
  UNIQUE (nombreLocal)
);
''')

print("Table registro_propietarios created successfully")

# Crear la tabla reserva
conn.execute('''
CREATE TABLE reserva (
  id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
  nombreLocal VARCHAR(100) NOT NULL,
  nombre_cliente VARCHAR(100) DEFAULT NULL,
  cantidad_personas INTEGER DEFAULT NULL,
  fecha_reserva DATE DEFAULT NULL,
  hora_reserva TIME DEFAULT NULL,
  comentarios TEXT DEFAULT NULL,
  id_usuario INTEGER NOT NULL,
  FOREIGN KEY (nombreLocal) REFERENCES nombre_local(nombreLocal),
  FOREIGN KEY (id_usuario) REFERENCES user(id)
);
''')

print("Table reserva created successfully")

# Crear la tabla user
conn.execute('''
CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL,
  password TEXT NOT NULL,
  fullname TEXT NOT NULL,
  id_rol INTEGER NOT NULL,
  FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);
''')

print("Table user created successfully")

conn.execute('''
CREATE TABLE roles (
  id_rol INTEGER PRIMARY KEY,
  descripcion VARCHAR(30) NOT NULL
);
''')

print("Table roles created successfully")

conn.close()
