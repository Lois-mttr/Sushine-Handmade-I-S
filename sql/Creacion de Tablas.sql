CREATE DATABASE  nexodb;
USE nexodb;

-- Tabla Categoría
create TABLE Categoria (
    idCategoria INT AUTO_INCREMENT PRIMARY KEY,
    nombreCategoria VARCHAR(25) NOT NULL,
    descripcionCategoria VARCHAR(100),
    estadoCategoria BIT NOT NULL DEFAULT 1
);

CREATE TABLE Ubicacion (
    id_ubicacion INT AUTO_INCREMENT PRIMARY KEY,
    nombreUbicacion VARCHAR(15) NOT NULL, -- 'Taller' o 'Sucursal'
    direccion VARCHAR(100)
);

Create TABLE Producto (
    id_producto VARCHAR(15), 
	idUbicacionPro INT NOT NULL,
    nombreProducto VARCHAR(30) NOT NULL,
    descripcionProducto VARCHAR(70),
    existenciaProducto INT NOT NULL,
    imagenProductoRuta varchar(250),
    idCategoriaPro INT,
    precioProducto DECIMAL (10,2),
    estado BIT NOT NULL DEFAULT 1,
    existenciaMinima INT DEFAULT 5,
    FOREIGN KEY (idCategoriaPro) REFERENCES Categoria(idCategoria),
    FOREIGN KEY (idUbicacionPro) REFERENCES Ubicacion(id_ubicacion),
    PRIMARY KEY (id_Producto, idUbicacionPro)
);

CREATE TABLE Persona(
cedula CHAR(16) PRIMARY KEY NOT NULL,
primerNombre VARCHAR(15) NOT NULL,
segundoNombre VARCHAR(15),
primerApellido VARCHAR(15) NOT NULL,
segundoApellido VARCHAR(15),
direccion VARCHAR(50) NOT NULL, 
estadoPersona BIT NOT NULL DEFAULT 1
);

CREATE Table Cliente (
idCliente INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
correo VARCHAR(30),
idPersonaCliente char(16),
foreign key  (idPersonaCliente) references Persona(cedula),
estadoCliente BIT NOT NULL DEFAULT 1
);

CREATE TABLE Empleado (
idEmpleado INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
rolEmpleado VARCHAR(30),
fechaContratacion DATETIME,
salario FLOAT,
correo VARCHAR(30),
idPersonaEmp char(16),
foreign key  (idPersonaEmp) references Persona(cedula),
estadoEmpleado BIT NOT NULL DEFAULT 1
);

CREATE TABLE Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombreUsuario VARCHAR(15) NOT NULL UNIQUE,
    passUsuario CHAR(64) NOT NULL,
    rol varchar(30),
    activo BIT DEFAULT 1,
    idEmpUsuario int,
    foreign key (idEmpUsuario) references Empleado(idEmpleado)
);

CREATE TABLE Venta (
    id_venta INT AUTO_INCREMENT PRIMARY KEY,
    fechaVenta DATETIME DEFAULT NOW(),
    total DECIMAL(10,2),
    estado ENUM('REALIZADA', 'ANULADA') DEFAULT 'REALIZADA',
    idUsuarioVenta int,
    codCliente int,
    FOREIGN KEY (idUsuarioVenta) REFERENCES Usuario(idUsuario),
    FOREIGN KEY (codCliente) REFERENCES Cliente(idCliente)
);


CREATE TABLE DetalleVenta (
    idVenta INT NOT NULL,
    idProVenta VARCHAR(15),
    cantidadVenta INT,
    subtotal DECIMAL(10,2),
    FOREIGN KEY (idVenta) REFERENCES Venta(id_Venta),
	FOREIGN KEY (idProVenta) REFERENCES Producto(id_producto),
    PRIMARY KEY (idVenta, idProVenta)
);


CREATE TABLE Devolucion (
    idDevolucion INT AUTO_INCREMENT PRIMARY KEY,
    idVentaDev INT NOT NULL,
	fechaDevolucion DATE,
    motivo TEXT,
    FOREIGN KEY (idVentaDev) REFERENCES Venta(id_Venta)
);

CREATE TABLE DetalleDevolucion (
    id_devolucion INT NOT NULL,
    id_producto VARCHAR(15) NOT NULL,
    cantidadDevuelta INT NOT NULL,
    FOREIGN KEY (id_devolucion) REFERENCES Devolucion(idDevolucion),
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto),
    PRIMARY KEY (id_devolucion, id_producto)
);

CREATE TABLE ProductosProduccion(
idProduccion INT AUTO_INCREMENT PRIMARY KEY,
fechaEntrada DATE NOT NULL,
observacion TEXT,
id_usuario INT,
EstadoRegistro BIT DEFAULT 1,
FOREIGN KEY (id_usuario) REFERENCES Usuario(idUsuario)
);

CREATE TABLE DetalleProduccion (
    id_produccion INT NOT NULL,
    id_producto VARCHAR(15) NOT NULL,
    cantidad INT NOT NULL,
    costo_unitario DECIMAL(10,2) NOT NULL,
    idFabricante int,
    FOREIGN KEY (idFabricante) REFERENCES Empleado(idEmpleado),
    FOREIGN KEY (id_produccion) REFERENCES ProductosProduccion(idProduccion),
    FOREIGN KEY (id_producto) REFERENCES Producto(id_producto),
    PRIMARY KEY (id_produccion, id_producto)
);

DELETE FROM ProductosProduccion
DELETE FROM DetalleProduccion
