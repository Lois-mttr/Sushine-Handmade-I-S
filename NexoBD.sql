CREATE DATABASE NEXODB
-- USE NEXODB
-- Tabla Categoría
CREATE TABLE Categoria (
    idCategoria INT AUTO_INCREMENT PRIMARY KEY,
    nombreCategoria VARCHAR(25) NOT NULL,
    descripcionCategoria VARCHAR(100),
    estadoCategoria BIT NOT NULL DEFAULT 1
);

-- Tabla Ubicación
CREATE TABLE Ubicacion (
    id_ubicacion INT AUTO_INCREMENT PRIMARY KEY,
    nombreUbicacion VARCHAR(15) NOT NULL, -- 'Taller' o 'Sucursal'
    direccion VARCHAR(100)
);

-- Tabla Producto de Prueba
CREATE TABLE Producto (
    id_producto VARCHAR(15) PRIMARY KEY, 
    nombreProducto VARCHAR(30) NOT NULL,
    descripcionProducto NVARCHAR(70),
    existenciaProducto INT NOT NULL,
    imagenProducto BLOB,
    idUbicacionPro INT NOT NULL,
    idCategoriaPro INT,
    estado BIT NOT NULL DEFAULT 1,
    FOREIGN KEY (idCategoriaPro) REFERENCES Categoria(idCategoria),
    FOREIGN KEY (idUbicacionPro) REFERENCES Ubicacion(id_ubicacion)
);


CREATE TABLE Persona(
cedula CHAR(16) PRIMARY KEY NOT NULL,
primerNombre NVARCHAR(15) NOT NULL,
segundoNombre NVARCHAR(15),
primerApellido NVARCHAR(15) NOT NULL,
segundoApellido NVARCHAR(15),
direccion NVARCHAR(50) NOT NULL
);

INSERT INTO Persona (cedula, primerNombre, primerApellido, direccion)
VALUES ('123-456789-0001X', 'Campary','Ramirez', 'Direccion General');


CREATE Table Cliente (
idCliente INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
correo NVARCHAR(30),
idPersonaCliente char(16),
foreign key  (idPersonaCliente) references Persona(cedula)
);

CREATE TABLE Empleado (
idEmpleado INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
rolEmpleado NVARCHAR(30),
fechaContratacion DATETIME,
salario FLOAT,
correo NVARCHAR(30),
idPersonaEmp char(16),
foreign key  (idPersonaEmp) references Persona(cedula)
);

-- Empleado de la Luisa (Campary)
INSERT INTO Empleado (rolEmpleado, fechaContratacion, salario, correo, idPersonaEmp)
VALUES ('Gerente General', '2015-01-15', 1200.50, 'Campary@gmail.com', '123-456789-0001X');

UPDATE Empleado
SET correo = 'camparyramirez@gmail.com'
WHERE idPersonaEmp = '2';

-- Tabla Usuario
CREATE TABLE Usuario (
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombreUsuario VARCHAR(15) NOT NULL UNIQUE,
    passUsuario VARCHAR(30) NOT NULL,
    rol varchar(30),
    activo BIT DEFAULT 1,
    idEmpUsuario int,
    foreign key (idEmpUsuario) references Empleado(idEmpleado)
);

select * from Usuario
-- CIFRADO DE CONTRASEÑA

DELIMITER $$

CREATE PROCEDURE RegistrarUsuario (
    IN p_nombreUsuario VARCHAR(15),
    IN p_contrasena VARCHAR(64),
    IN p_rol VARCHAR(30),
    IN p_idEmpleado INT
)
BEGIN
    INSERT INTO Usuario (nombreUsuario, passUsuario, rol, activo, idEmpUsuario)
    VALUES (
        p_nombreUsuario,
        SHA2(p_contrasena, 256),
        p_rol,
        1,
        p_idEmpleado
    );
END$$

DELIMITER ;
-- Funcionamiento
CALL RegistrarUsuario('Campary', 'Camp*2520', 'admin', 2);

SELECT idEmpleado FROM Empleado;

-- Tabla Venta
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



-- Tabla Detalle de Venta
CREATE TABLE DetalleVenta (
    idVenta INT NOT NULL,
    idProVenta VARCHAR(15),
    cantidadVenta INT,
    subtotal DECIMAL(10,2),
    FOREIGN KEY (idVenta) REFERENCES Venta(id_Venta),
	FOREIGN KEY (idProVenta) REFERENCES Producto(id_producto),
    PRIMARY KEY (idVenta, idProVenta)
);

-- Tabla Devolución
CREATE TABLE Devolucion (
    idDevolucion INT AUTO_INCREMENT PRIMARY KEY,
    idVentaDev INT NOT NULL,
	fechaDevolucion DATE,
    motivo TEXT,
    FOREIGN KEY (idVentaDev) REFERENCES Venta(id_Venta)
);

-- Tabla Detalle de Devolución
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
