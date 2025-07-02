CREATE DATABASE  nexodb;
USE nexodb;
---------------------------------------------------------------------
-- PROCEDIMIENTOS TABLA PRODUCTO
---------------------------------------------------------------------
/*PROCEDIMIENTO INSERCCION DE PRODUCTO*/
CATEGORIA UBICACION
DELIMITER //
CREATE PROCEDURE InsertarProducto(
    IN p_id_producto VARCHAR(15),
    IN p_idUbicacionPro INT,
    IN p_nombreProducto VARCHAR(30),
    IN p_descripcionProducto VARCHAR(70),
    IN p_existenciaProducto INT,
    IN p_imagenProductoRuta VARCHAR(500),
    IN p_idCategoriaPro INT,
    IN p_precioProducto DECIMAL(10,2)
)
BEGIN
    DECLARE v_count INT;
    DECLARE v_errorMsg VARCHAR(255);

    -- Validación de formato del ID de producto
    IF p_id_producto NOT REGEXP '^[A-Za-z]{4}[0-9]{4}$' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Formato de ID de producto inválido. Debe ser 4 letras y 4 números.';
    END IF;

    -- Validar existencia de la ubicación
     IF NOT EXISTS (SELECT 1 FROM Ubicacion WHERE id_ubicacion = p_idUbicacionPro) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ubicación no válida.';
    END IF;

    -- Validar existencia de la categoría
     IF NOT EXISTS (SELECT 1 FROM Categoria WHERE idCategoria = p_idCategoriaPro) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Categoría no válida.';
    END IF;

    -- Validar existencia > 0
    IF p_existenciaProducto <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La existencia debe ser mayor a 0.';
    END IF;

    -- Validar precio > 0
    IF p_precioProducto <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El precio debe ser mayor a 0.';
    END IF;

    -- Insertar producto
    INSERT INTO Producto (
        id_producto, idUbicacionPro, nombreProducto, descripcionProducto,
        existenciaProducto, imagenProductoRuta, idCategoriaPro, precioProducto, estado
    )
    VALUES (
        p_id_producto, p_idUbicacionPro, p_nombreProducto, p_descripcionProducto,
        p_existenciaProducto, p_imagenProductoRuta, p_idCategoriaPro, p_precioProducto, 1
    );
END //
DELIMITER ;

-- Crear
CALL InsertarProducto('BOLS0001', 1, 'Bolso cuero café', 'Hecho a mano', 10, '/imagenes/bolso1.jpg', 2, 35.50);
CALL InsertarProducto('BOLS0001', 2, 'Bolso cuero café', 'Hecho a mano', 10, '/imagenes/bolso1.jpg', 2, 35.50);

/*PROCEDIMIENTO EDITAR PRODUCTO*/

DELIMITER //

CREATE PROCEDURE EditarProducto(
    IN p_id_producto VARCHAR(15),
    IN p_idUbicacionPro INT,
    IN p_nombreProducto VARCHAR(30),
    IN p_descripcionProducto VARCHAR(70),
    IN p_existenciaProducto INT,
    IN p_imagenProductoRuta VARCHAR(500),
    IN p_idCategoriaPro INT,
    IN p_precioProducto DECIMAL(10,2)
)
BEGIN
    -- Verificar existencia del producto 
    IF NOT EXISTS (SELECT 1 FROM Producto WHERE id_producto = p_id_producto AND idUbicacionPro = p_idUbicacionPro) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El producto no existe en esa ubicación.';
    END IF;

    -- Validar existencia de la ubicación  
    IF NOT EXISTS (SELECT 1 FROM Ubicacion WHERE id_ubicacion = p_idUbicacionPro) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Ubicación no válida.';
    END IF;

    -- Validar existencia de la categoría  
    IF NOT EXISTS (SELECT 1 FROM Categoria WHERE idCategoria = p_idCategoriaPro) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Categoría no válida.';
    END IF;

    -- Validar existencia > 0
    IF p_existenciaProducto <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La existencia debe ser mayor a 0.';
    END IF;

    -- Validar precio > 0
    IF p_precioProducto <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El precio debe ser mayor a 0.';
    END IF;

    -- Actualizar producto
    UPDATE Producto
    SET
        nombreProducto = p_nombreProducto,
        descripcionProducto = p_descripcionProducto,
        existenciaProducto = p_existenciaProducto,
        imagenProductoRuta = p_imagenProductoRuta,
        idCategoriaPro = p_idCategoriaPro,
        precioProducto = p_precioProducto
    WHERE
        id_producto = p_id_producto AND idUbicacionPro = p_idUbicacionPro;
END //
DELIMITER ;

/*PROCEDIMIENTO DAR DE BAJA PRODUCTO*/

DELIMITER //
CREATE PROCEDURE EliminarProducto(
    IN p_id_producto VARCHAR(15),
    IN p_idUbicacionPro INT
)
BEGIN
    -- Validar existencia del producto  
    IF NOT EXISTS (SELECT 1 FROM Producto WHERE id_producto = p_id_producto AND idUbicacionPro = p_idUbicacionPro) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El producto no existe.';
    END IF;

    -- Cambiar estado a inactivo (0)
    UPDATE Producto
    SET estado = 0
    WHERE id_producto = p_id_producto AND idUbicacionPro = p_idUbicacionPro;
END //
DELIMITER ;

---------------------------------------------------------------------
-- PROCEDIMIENTOS TABLA PERSONA
---------------------------------------------------------------------
/*INSERCCION EN TABLA PERSONA*/
DELIMITER //
CREATE PROCEDURE InsertarPersona(
    IN p_cedula CHAR(16),
    IN p_primerNombre VARCHAR(15),
    IN p_segundoNombre VARCHAR(15),
    IN p_primerApellido VARCHAR(15),
    IN p_segundoApellido VARCHAR(15),
    IN p_direccion VARCHAR(50)
)
BEGIN
    -- Validar formato de la cédula (13 números seguidos de una letra)
    IF p_cedula NOT REGEXP '^[0-9]{13}[A-Za-z]$' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Formato de cédula inválido. Debe contener 13 números seguidos de una letra.';
    END IF;

    -- Validar que la cédula no exista ya
    IF EXISTS (SELECT 1 FROM Persona WHERE cedula = p_cedula) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cédula ya existe.';
    END IF;

    -- Insertar la persona
    INSERT INTO Persona (cedula, primerNombre, segundoNombre, primerApellido, segundoApellido, direccion, estadoPersona)
    VALUES (p_cedula, p_primerNombre, p_segundoNombre, p_primerApellido, p_segundoApellido, p_direccion, 1);

END //
DELIMITER ;

/*PROCEDIMIENTO EDITAR PERSONA*/

DELIMITER //
CREATE PROCEDURE EditarPersona(
    IN p_cedula CHAR(16),
    IN p_primerNombre VARCHAR(15),
    IN p_segundoNombre VARCHAR(15),
    IN p_primerApellido VARCHAR(15),
    IN p_segundoApellido VARCHAR(15),
    IN p_direccion VARCHAR(50)
)
BEGIN
    -- Validar que la cédula exista
    IF NOT EXISTS (SELECT 1 FROM Persona WHERE cedula = p_cedula) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cédula no existe.';
    END IF;

    -- Actualizar la persona
    UPDATE Persona
    SET
        primerNombre = p_primerNombre,
        segundoNombre = p_segundoNombre,
        primerApellido = p_primerApellido,
        segundoApellido = p_segundoApellido,
        direccion = p_direccion
    WHERE
        cedula = p_cedula;

END //
DELIMITER ;

/*PROCEDIMIENTO ELIMINAR PERSONA*/

DELIMITER //
CREATE PROCEDURE EliminarPersona(
    IN p_cedula CHAR(16)
)
BEGIN
    -- Validar que la cédula exista
    IF NOT EXISTS (SELECT 1 FROM Persona WHERE cedula = p_cedula) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La cédula no existe.';
    END IF;

    -- Desactivar la persona (cambiar estadoPersona a 0)
    UPDATE Persona
    SET estadoPersona = 0
    WHERE cedula = p_cedula;

END //
DELIMITER ;

---------------------------------------------------------------------
-- PROCEDIMIENTOS TABLA CLIENTE
---------------------------------------------------------------------

/*PROCEDIMIENTO INSERTAR CLIENTE*/

DELIMITER //
CREATE PROCEDURE InsertarCliente(
    IN p_correo VARCHAR(30),
    IN p_idPersonaCliente CHAR(16)
)
BEGIN
    -- Validar que la persona exista en la tabla Persona
    IF NOT EXISTS (SELECT 1 FROM Persona WHERE cedula = p_idPersonaCliente) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La persona con la cédula especificada no existe.';
    END IF;

    -- Validar que el correo no exista ya para otro cliente
    IF EXISTS (SELECT 1 FROM Cliente WHERE correo = p_correo) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El correo electrónico ya está asociado a otro cliente.';
    END IF;

    -- Insertar el cliente
    INSERT INTO Cliente (correo, idPersonaCliente, estadoCliente)
    VALUES (p_correo, p_idPersonaCliente, 1);

END //
DELIMITER ;

/*PROCEDIMIENTO EDITAR CLIENTE*/

DELIMITER //
CREATE PROCEDURE EditarCliente(
    IN p_idCliente INT,
    IN p_correo VARCHAR(30),
    IN p_idPersonaCliente CHAR(16)
)
BEGIN
    -- Validar que el cliente exista
    IF NOT EXISTS (SELECT 1 FROM Cliente WHERE idCliente = p_idCliente) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El cliente con el ID especificado no existe.';
    END IF;

    -- Validar que la persona exista en la tabla Persona
    IF NOT EXISTS (SELECT 1 FROM Persona WHERE cedula = p_idPersonaCliente) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La persona con la cédula especificada no existe.';
    END IF;

    -- Validar que el correo no exista ya para otro cliente (excepto el cliente actual)
    IF EXISTS (SELECT 1 FROM Cliente WHERE correo = p_correo AND idCliente != p_idCliente) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El correo electrónico ya está asociado a otro cliente.';
    END IF;

    -- Actualizar el cliente
    UPDATE Cliente
    SET
        correo = p_correo,
        idPersonaCliente = p_idPersonaCliente
    WHERE
        idCliente = p_idCliente;

END //
DELIMITER ;

/*PROCEDIMIENTO DAR DE BAJA CLIENTE*/

DELIMITER //
CREATE PROCEDURE EliminarCliente(
    IN p_idCliente INT
)
BEGIN
    -- Validar que el cliente exista
    IF NOT EXISTS (SELECT 1 FROM Cliente WHERE idCliente = p_idCliente) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El cliente con el ID especificado no existe.';
    END IF;

    -- Desactivar el cliente (cambiar estadoCliente a 0)
    UPDATE Cliente
    SET estadoCliente = 0
    WHERE idCliente = p_idCliente;

END //
DELIMITER ;

---------------------------------------------------------------------
-- PROCEDIMIENTOS TABLA EMPLEADO
---------------------------------------------------------------------

/*PROCEDIMIENTO INGRESAR EMPLEADO*/

DELIMITER //
CREATE PROCEDURE CrearEmpleado(
    IN p_rolEmpleado VARCHAR(30),
    IN p_fechaContratacion DATETIME,
    IN p_salario FLOAT,
    IN p_correo VARCHAR(30),
    IN p_idPersonaEmp CHAR(16)
)
BEGIN
    
    -- Validar salario positivo
    IF p_salario <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El salario debe ser mayor a 0.';
    END IF;

    -- Validar existencia de la persona
    IF NOT exists( SELECT 1 FROM Persona WHERE cedula = p_idPersonaEmp) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La persona indicada no existe.';
    END IF;

    -- Insertar nuevo empleado
    INSERT INTO Empleado (
        rolEmpleado, fechaContratacion, salario, correo, idPersonaEmp, estadoEmpleado
    )
    VALUES (
        p_rolEmpleado, p_fechaContratacion, p_salario, p_correo, p_idPersonaEmp, 1
    );
END //
DELIMITER ;

/*PROCEDIMIENTO EDITAR EMPLEADO*/

DELIMITER //
CREATE PROCEDURE EditarEmpleado(
    IN p_idEmpleado INT,
    IN p_rolEmpleado VARCHAR(30),
    IN p_fechaContratacion DATETIME,
    IN p_salario FLOAT,
    IN p_correo VARCHAR(30),
    IN p_idPersonaEmp CHAR(16)
)
BEGIN
    -- Verificar que el empleado exista
    IF NOT EXISTS (SELECT 1 FROM Empleado WHERE idEmpleado = p_idEmpleado) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El empleado no existe.';
    END IF;

    -- Validar salario
    IF p_salario <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El salario debe ser mayor a 0.';
    END IF;

    -- Validar existencia de persona
    IF NOT EXISTS (SELECT 1 FROM Persona WHERE cedula = p_idPersonaEmp) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La persona indicada no existe.';
    END IF;

    -- Actualizar datos
    UPDATE Empleado
    SET
        rolEmpleado = p_rolEmpleado,
        fechaContratacion = p_fechaContratacion,
        salario = p_salario,
        correo = p_correo,
        idPersonaEmp = p_idPersonaEmp
    WHERE idEmpleado = p_idEmpleado;
END //
DELIMITER ;

/*PROCEDIMIENTO DAR DE BAJA EMPLEADO*/
DELIMITER //
CREATE PROCEDURE EliminarEmpleado(
    IN p_idEmpleado INT
)
BEGIN
  
    -- Verificar existencia del empleado
    IF NOT EXISTS (SELECT 1 FROM Empleado WHERE idEmpleado = p_idEmpleado) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El empleado no existe.';
    END IF;

    -- Cambio de estado 
    UPDATE Empleado
    SET estadoEmpleado = 0
    WHERE idEmpleado = p_idEmpleado;
END //
DELIMITER ;


-- CIFRADO DE CONTRASEÑA
/PROCEDIMIENTO DE INGRESAR USUARIO Y CIFRAR CONTRASEÑA/

DELIMITER $$
CREATE PROCEDURE RegistrarUsuario (
    IN p_nombreUsuario VARCHAR(15),
    IN p_contrasena VARCHAR(64),
    IN p_rol VARCHAR(30),
    IN p_correo VARCHAR(50),
    IN p_idEmpleado INT
)
BEGIN
    INSERT INTO Usuario (
        nombreUsuario,
        passUsuario,
        rol,
        correo,
        activo,
        fecha_creacion,
        ultimo_login,
        intentos_fallidos,
        idEmpUsuario
    )
    VALUES (
        p_nombreUsuario,
        SHA2(p_contrasena, 256),
        p_rol,
        p_correo,
        1, -- activo por defecto
        CURRENT_TIMESTAMP, -- fecha de creación
        NULL, -- último login aún no ha ocurrido
        0, -- sin intentos fallidos al inicio
        p_idEmpleado
    );
END$$
DELIMITER ;

-- Funcionamiento
CALL RegistrarUsuario('Campary','Camp*2520','admin', 'luisacrossway@gmail.com',1);
CALL RegistrarUsuario('Maria','Maria*2520','encargado_sucursal','cinthiacarbajal1309052017@gmail.com','2')

-- FUNCIONAMIENTO--
-- Vista de Alertas por bajo Inventario
CREATE VIEW ProductosBajoStock AS
SELECT 
    id_producto, 
    idUbicacionPro AS ubicacion,
    nombreProducto,
    existenciaProducto,
    existenciaMinima
FROM Producto
WHERE existenciaProducto < existenciaMinima;

Select* from ProductosBajoStock 



---------------------------------------------------------------------
-- PROCEDIMIENTOS RELIZAR VENTA
---------------------------------------------------------------------

DELIMITER //
CREATE PROCEDURE RealizarVenta(
    IN p_idUsuarioVenta INT,
    IN p_codCliente INT,
    IN p_detalles JSON
)
BEGIN
    -- Declaración de variables
    DECLARE v_idVenta INT;
    DECLARE v_total DECIMAL(10,2) DEFAULT 0;
    DECLARE v_idProVenta VARCHAR(15);
    DECLARE v_cantidadVenta INT;
    DECLARE v_subtotal DECIMAL(10,2);
    DECLARE v_stockDisponible INT;
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_errorMsg VARCHAR(255);

    -- Cursor para recorrer los detalles
    DECLARE cur CURSOR FOR 
        SELECT idProVenta, cantidadVenta 
        FROM JSON_TABLE(p_detalles, '$[*]' 
            COLUMNS (
                idProVenta VARCHAR(15) PATH '$.idProVenta', 
                cantidadVenta INT PATH '$.cantidadVenta'
            )
        ) AS detalles;

    -- Handler
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Validación: cliente existente
    IF NOT EXISTS (SELECT 1 FROM Cliente WHERE idCliente = p_codCliente) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El cliente no existe.';
    END IF;

    -- Validación: usuario existente
    IF NOT EXISTS (SELECT 1 FROM Usuario WHERE idUsuario = p_idUsuarioVenta) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario no existe.';
    END IF;

    -- Validación: detalles no vacíos
    IF JSON_LENGTH(p_detalles) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Los detalles de la venta no pueden estar vacíos.';
    END IF;

    -- Iniciar transacción
    START TRANSACTION;

    -- Insertar encabezado de venta
    INSERT INTO Venta (idUsuarioVenta, codCliente, total)
    VALUES (p_idUsuarioVenta, p_codCliente, 0);

    SET v_idVenta = LAST_INSERT_ID();

    -- Abrir cursor
    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_idProVenta, v_cantidadVenta;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Verificar stock en la sucursal (ubicación 2)
        SELECT existenciaProducto INTO v_stockDisponible 
        FROM Producto 
        WHERE id_producto = v_idProVenta AND idUbicacionPro = 2;

        IF v_stockDisponible IS NULL OR v_stockDisponible < v_cantidadVenta THEN
            ROLLBACK;
            SET v_errorMsg = CONCAT('Stock insuficiente para el producto ', v_idProVenta);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Calcular subtotal con impuesto incluido
        SET v_subtotal = (
            SELECT precioProducto 
            FROM Producto 
            WHERE id_producto = v_idProVenta AND idUbicacionPro = 2
        ) * v_cantidadVenta * 1.15;

        -- Insertar detalle
        INSERT INTO DetalleVenta (idVenta, idProVenta, cantidadVenta, subtotal)
        VALUES (v_idVenta, v_idProVenta, v_cantidadVenta, v_subtotal);

        -- Actualizar stock
        UPDATE Producto
        SET existenciaProducto = existenciaProducto - v_cantidadVenta
        WHERE id_producto = v_idProVenta AND idUbicacionPro = 2;

        -- Acumular total
        SET v_total = v_total + v_subtotal;
    END LOOP;

    CLOSE cur;

    -- Actualizar total en encabezado de venta
    UPDATE Venta
    SET total = v_total
    WHERE id_venta = v_idVenta;

    COMMIT;
END //
DELIMITER ;

CALL RealizarVenta(
  1, -- Usuario Venta
  2, -- Usuario Cliente
  '[{"idProVenta": "PROD001", "cantidadVenta": 1}, {"idProVenta": "PROD002", "cantidadVenta": 1}]'
);

/*PROCEDIMIENTO EDITAR VENTA*/

DELIMITER //
CREATE PROCEDURE EditarVenta(
    IN p_idVenta INT,
    IN p_idUsuario INT,
    IN p_detalles JSON
)
BEGIN
    DECLARE v_idProVenta VARCHAR(15);
    DECLARE v_cantidadVenta INT;
    DECLARE v_subtotal DECIMAL(10,2);
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_total DECIMAL(10,2) DEFAULT 0;
    DECLARE v_stock INT;
    DECLARE v_errorMsg VARCHAR(255);

    -- Cursor para nuevos detalles
    DECLARE cur CURSOR FOR 
        SELECT idProVenta, cantidadVenta
        FROM JSON_TABLE(p_detalles, '$[*]'
            COLUMNS (
                idProVenta VARCHAR(15) PATH '$.idProVenta',
                cantidadVenta INT PATH '$.cantidadVenta'
            )
        ) AS detalles;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Verificar que la venta existe y no esté anulada
    IF NOT EXISTS (
        SELECT 1 FROM Venta
        WHERE id_venta = p_idVenta AND estado = 'REALIZADA'
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La venta no existe o ya fue anulada.';
    END IF;

    START TRANSACTION;

    -- 1. Devolver el stock anterior
    UPDATE Producto p
    JOIN DetalleVenta dv ON p.id_producto = dv.idProVenta AND p.idUbicacionPro = 2
    SET p.existenciaProducto = p.existenciaProducto + dv.cantidadVenta
    WHERE dv.idVenta = p_idVenta;

    -- 2. Borrar detalles anteriores
    DELETE FROM DetalleVenta WHERE idVenta = p_idVenta;

    -- 3. Aplicar nuevos productos
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_idProVenta, v_cantidadVenta;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Validar stock
        SELECT existenciaProducto INTO v_stock
        FROM Producto
        WHERE id_producto = v_idProVenta AND idUbicacionPro = 2;

        IF v_stock IS NULL OR v_stock < v_cantidadVenta THEN
            ROLLBACK;
            SET v_errorMsg = CONCAT('Stock insuficiente para producto ', v_idProVenta);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Calcular subtotal con impuesto
        SET v_subtotal = (
            SELECT precioProducto FROM Producto
            WHERE id_producto = v_idProVenta AND idUbicacionPro = 2
        ) * v_cantidadVenta * 1.15;

        -- Insertar nuevo detalle
        INSERT INTO DetalleVenta (idVenta, idProVenta, cantidadVenta, subtotal)
        VALUES (p_idVenta, v_idProVenta, v_cantidadVenta, v_subtotal);

        -- Restar nuevo stock
        UPDATE Producto
        SET existenciaProducto = existenciaProducto - v_cantidadVenta
        WHERE id_producto = v_idProVenta AND idUbicacionPro = 2;

        -- Acumular total
        SET v_total = v_total + v_subtotal;
    END LOOP;
    CLOSE cur;

    -- 4. Actualizar total
    UPDATE Venta SET total = v_total WHERE id_venta = p_idVenta;

    COMMIT;
END //
DELIMITER ;

/*PROCEDIMIENTO ANULAR VENTA*/

DELIMITER //
CREATE PROCEDURE AnularVenta(
    IN p_idVenta INT
)
BEGIN
    DECLARE v_count INT;

    -- Validar existencia y estado
    SELECT COUNT(*) INTO v_count
    FROM Venta WHERE id_venta = p_idVenta AND estado = 'REALIZADA';

    IF v_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Venta no existe o ya está anulada.';
    END IF;

    START TRANSACTION;

    -- Devolver stock por producto
    UPDATE Producto p
    JOIN DetalleVenta dv ON p.id_producto = dv.idProVenta AND p.idUbicacionPro = 2
    SET p.existenciaProducto = p.existenciaProducto + dv.cantidadVenta
    WHERE dv.idVenta = p_idVenta;

    -- Cambiar estado
    UPDATE Venta SET estado = 'ANULADA' WHERE id_venta = p_idVenta;

    COMMIT;
END //
DELIMITER ;

---------------------------------------------------------------------
-- PROCEDIMIENTOS RELIZAR DEVOLUCION
---------------------------------------------------------------------

/*PROCEDIMIENTO INGRESAR DEVOLUCION*/

DELIMITER //
CREATE PROCEDURE RegistrarDevolucion(
    IN p_idVentaDev INT,
    IN p_fecha DATE,
    IN p_motivo TEXT,
    IN p_detalles JSON
)
BEGIN
    DECLARE v_idDevolucion INT;
    DECLARE v_idProducto VARCHAR(15);
    DECLARE v_cantidadDevuelta INT;
    DECLARE v_cantidadVendida INT;
    DECLARE v_cantidadYaDevuelta INT DEFAULT 0;
    DECLARE v_errorMensaje VARCHAR(255);
    DECLARE done INT DEFAULT FALSE;

    -- Cursor para iterar los productos devueltos
    DECLARE cur CURSOR FOR 
        SELECT id_producto, cantidadDevuelta
        FROM JSON_TABLE(p_detalles, '$[*]'
            COLUMNS (
                id_producto VARCHAR(15) PATH '$.id_producto',
                cantidadDevuelta INT PATH '$.cantidadDevuelta'
            )
        ) AS detalles;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;

    -- Verificar que la venta esté REALIZADA
    IF NOT EXISTS (
        SELECT 1 FROM Venta
        WHERE id_venta = p_idVentaDev AND estado = 'REALIZADA'
    ) THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La venta no existe o ya fue anulada.';
    END IF;

    -- Insertar encabezado en Devolucion
    INSERT INTO Devolucion (idVentaDev, fechaDevolucion, motivo)
    VALUES (p_idVentaDev, p_fecha, p_motivo);

    SET v_idDevolucion = LAST_INSERT_ID();

    -- Procesar cada producto devuelto
    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_idProducto, v_cantidadDevuelta;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- 1. Verificar que el producto fue parte de la venta
        SELECT cantidadVenta INTO v_cantidadVendida
        FROM DetalleVenta
        WHERE idVenta = p_idVentaDev AND idProVenta = v_idProducto;

        IF v_cantidadVendida IS NULL THEN
            ROLLBACK;
            SET v_errorMensaje = CONCAT('El producto ', v_idProducto, ' no está en la venta.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMensaje;
        END IF;

        -- 2. Obtener cantidad ya devuelta previamente
        SELECT IFNULL(SUM(cantidadDevuelta), 0) INTO v_cantidadYaDevuelta
        FROM DetalleDevolucion
        WHERE id_devolucion IN (
            SELECT idDevolucion FROM Devolucion WHERE idVentaDev = p_idVentaDev
        )
        AND id_producto = v_idProducto;

        -- 3. Verificar que no se exceda lo vendido
        IF v_cantidadDevuelta + v_cantidadYaDevuelta > v_cantidadVendida THEN
            ROLLBACK;
            SET v_errorMensaje = CONCAT('Cantidad devuelta excede lo vendido para el producto ', v_idProducto);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMensaje;
        END IF;

        -- 4. Insertar detalle de devolución
        INSERT INTO DetalleDevolucion (id_devolucion, id_producto, cantidadDevuelta)
        VALUES (v_idDevolucion, v_idProducto, v_cantidadDevuelta);

        -- 5. Aumentar stock en sucursal (idUbicacionPro = 2)
        UPDATE Producto
        SET existenciaProducto = existenciaProducto + v_cantidadDevuelta
        WHERE id_producto = v_idProducto
          AND idUbicacionPro = 2;
    END LOOP;

    CLOSE cur;

    -- 6. Anular la venta original
    UPDATE Venta
    SET estado = 'ANULADA'
    WHERE id_venta = p_idVentaDev;

    COMMIT;
END //
DELIMITER ;

/*PROCEDIMIENTO EDITAR DEVOLUCION*/

DELIMITER //
CREATE PROCEDURE EditarDevolucion(
    IN p_idDevolucion INT,
    IN p_nuevaFecha DATE,
    IN p_nuevoMotivo TEXT,
    IN p_nuevosDetalles JSON
)
BEGIN
    DECLARE v_idProducto VARCHAR(15);
    DECLARE v_cantidadDevuelta INT;
    DECLARE v_idVenta INT;
    DECLARE v_cantidadVendida INT;
    DECLARE v_cantidadDevAnterior INT;
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_errorMsg VARCHAR(255);

    -- Cursor para recorrer los nuevos productos
    DECLARE cur CURSOR FOR
        SELECT id_producto, cantidadDevuelta
        FROM JSON_TABLE(p_nuevosDetalles, '$[*]'
            COLUMNS (
                id_producto VARCHAR(15) PATH '$.id_producto',
                cantidadDevuelta INT PATH '$.cantidadDevuelta'
            )
        ) AS detalle;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Verificar que la devolución exista
    IF NOT EXISTS (
        SELECT 1 FROM Devolucion WHERE idDevolucion = p_idDevolucion
    ) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La devolución no existe.';
    END IF;

    -- Obtener la venta relacionada
    SELECT idVentaDev INTO v_idVenta
    FROM Devolucion
    WHERE idDevolucion = p_idDevolucion;

    START TRANSACTION;

    -- 1. Devolver stock previamente sumado
    UPDATE Producto p
    JOIN DetalleDevolucion dd ON p.id_producto = dd.id_producto AND p.idUbicacionPro = 2
    SET p.existenciaProducto = p.existenciaProducto - dd.cantidadDevuelta
    WHERE dd.id_devolucion = p_idDevolucion;

    -- 2. Eliminar detalles anteriores
    DELETE FROM DetalleDevolucion WHERE id_devolucion = p_idDevolucion;

    -- 3. Actualizar encabezado de devolución
    UPDATE Devolucion
    SET fechaDevolucion = p_nuevaFecha, motivo = p_nuevoMotivo
    WHERE idDevolucion = p_idDevolucion;

    -- 4. Procesar nuevos productos devueltos
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_idProducto, v_cantidadDevuelta;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Verificar que el producto estuvo en la venta
        SELECT cantidadVenta INTO v_cantidadVendida
        FROM DetalleVenta
        WHERE idVenta = v_idVenta AND idProVenta = v_idProducto;

        IF v_cantidadVendida IS NULL THEN
            SET v_errorMsg = CONCAT('El producto ', v_idProducto, ' no forma parte de la venta.');
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Verificar que la cantidad no exceda lo vendido menos otras devoluciones
        SELECT IFNULL(SUM(cantidadDevuelta), 0) INTO v_cantidadDevAnterior
        FROM DetalleDevolucion
        WHERE id_producto = v_idProducto
        AND id_devolucion IN (
            SELECT idDevolucion FROM Devolucion
            WHERE idVentaDev = v_idVenta AND idDevolucion != p_idDevolucion
        );

        IF v_cantidadDevuelta + v_cantidadDevAnterior > v_cantidadVendida THEN
            SET v_errorMsg = CONCAT('Cantidad devuelta excede lo vendido para el producto ', v_idProducto);
            ROLLBACK;
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Insertar nuevo detalle
        INSERT INTO DetalleDevolucion (id_devolucion, id_producto, cantidadDevuelta)
        VALUES (p_idDevolucion, v_idProducto, v_cantidadDevuelta);

        -- Aumentar stock en sucursal
        UPDATE Producto
        SET existenciaProducto = existenciaProducto + v_cantidadDevuelta
        WHERE id_producto = v_idProducto AND idUbicacionPro = 2;
    END LOOP;
    CLOSE cur;

    COMMIT;
END //
DELIMITER ;


CALL RegistrarDevolucion(
    1,  -- id de la venta original
    CURDATE(),
    'El cliente devolvió productos defectuosos',
    JSON_ARRAY(
        JSON_OBJECT('id_producto', 'PROD001', 'cantidadDevuelta', 1),
        JSON_OBJECT('id_producto', 'PROD002', 'cantidadDevuelta', 1)
    )
);
select * from Venta;
Select * from DetalleVenta;
select * from Producto

---------------------------------------------------------------------
-- PROCEDIMIENTOS RELIZAR INGRESO DE PRODUCTOS
---------------------------------------------------------------------

DELIMITER //
CREATE PROCEDURE RegistrarProduccion(
    IN p_fechaEntrada DATE,
    IN p_observacion TEXT,
    IN p_idUsuario INT,
    IN p_detalles JSON
)
BEGIN
    DECLARE v_idProduccion INT;
    DECLARE v_idProducto VARCHAR(15);
    DECLARE v_cantidad INT;
    DECLARE v_costo DECIMAL(10,2);
    DECLARE v_idFabricante INT;
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_errorMensaje VARCHAR(255);
    DECLARE v_count INT;

    -- Cursor para recorrer el JSON
    DECLARE cur CURSOR FOR 
        SELECT id_producto, cantidad, costo_unitario, idFabricante
        FROM JSON_TABLE(p_detalles, '$[*]'
            COLUMNS (
                id_producto VARCHAR(15) PATH '$.id_producto',
                cantidad INT PATH '$.cantidad',
                costo_unitario DECIMAL(10,2) PATH '$.costo_unitario',
                idFabricante INT PATH '$.idFabricante'
            )
        ) AS detalles;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Validar que el usuario existe
    IF NOT EXISTS (SELECT 1 FROM Usuario WHERE idUsuario = p_idUsuario) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario indicado no existe.';
    END IF;

    START TRANSACTION;

    -- Insertar encabezado de producción
    INSERT INTO ProductosProduccion (fechaEntrada, observacion, id_usuario)
    VALUES (p_fechaEntrada, p_observacion, p_idUsuario);

    SET v_idProduccion = LAST_INSERT_ID();

    -- Procesar cada producto
    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO v_idProducto, v_cantidad, v_costo, v_idFabricante;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Validar que el producto existe en taller (ubicación 1)
        IF NOT EXISTS (SELECT 1 FROM Producto
        WHERE id_producto = v_idProducto AND idUbicacionPro = 1) THEN
            ROLLBACK;
            SET v_errorMensaje = CONCAT('El producto ', v_idProducto, ' no existe en el taller.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMensaje;
        END IF;

        -- Validar cantidad > 0
        IF v_cantidad <= 0 THEN
            ROLLBACK;
            SET v_errorMensaje = CONCAT('La cantidad debe ser mayor a 0 para el producto ', v_idProducto);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMensaje;
        END IF;

        -- Validar costo_unitario > 0
        IF v_costo <= 0 THEN
            ROLLBACK;
            SET v_errorMensaje = CONCAT('El costo unitario debe ser mayor a 0 para el producto ', v_idProducto);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMensaje;
        END IF;

        -- Validar que el fabricante (empleado) exista
        IF NOT EXISTS (SELECT 1 FROM Empleado WHERE idEmpleado = v_idFabricante)THEN
            ROLLBACK;
            SET v_errorMensaje = CONCAT('El empleado (fabricante) con ID ', v_idFabricante, ' no existe.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMensaje;
        END IF;

        -- Insertar detalle de producción
        INSERT INTO DetalleProduccion (
            id_produccion, id_producto, cantidad, costo_unitario, idFabricante
        )
        VALUES (
            v_idProduccion, v_idProducto, v_cantidad, v_costo, v_idFabricante
        );

        -- Aumentar stock en taller
        UPDATE Producto
        SET existenciaProducto = existenciaProducto + v_cantidad
        WHERE id_producto = v_idProducto AND idUbicacionPro = 1;
    END LOOP;

    CLOSE cur;

    COMMIT;
END //
DELIMITER ;

/*PROCEDIMIENTO DE EDITAR REGISTRO DE PRODUCCION*/

DELIMITER //
CREATE PROCEDURE EditarProduccion(
    IN p_idProduccion INT,
    IN p_fechaEntrada DATE,
    IN p_observacion TEXT,
    IN p_idUsuario INT,
    IN p_detalles JSON
)
BEGIN
    DECLARE v_idProducto VARCHAR(15);
    DECLARE v_cantidad INT;
    DECLARE v_costo DECIMAL(10,2);
    DECLARE v_idFabricante INT;
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_errorMsg VARCHAR(255);


    -- Cursor
    DECLARE cur CURSOR FOR
        SELECT id_producto, cantidad, costo_unitario, idFabricante
        FROM JSON_TABLE(p_detalles, '$[*]'
            COLUMNS (
                id_producto VARCHAR(15) PATH '$.id_producto',
                cantidad INT PATH '$.cantidad',
                costo_unitario DECIMAL(10,2) PATH '$.costo_unitario',
                idFabricante INT PATH '$.idFabricante'
            )
        ) AS detalles;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Validar que la producción existe y está activa
    IF NOT EXISTS (SELECT 1 FROM ProductosProduccion
    WHERE idProduccion = p_idProduccion AND EstadoRegistro = 1) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'La producción no existe o está inactiva.';
    END IF;

    -- Validar usuario
    IF NOT EXISTS ( SELECT 1 FROM Usuario WHERE idUsuario = p_idUsuario) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El usuario no existe.';
    END IF;

    START TRANSACTION;

    -- Revertir stock anterior
    UPDATE Producto p
    JOIN DetalleProduccion dp ON p.id_producto = dp.id_producto AND p.idUbicacionPro = 1
    SET p.existenciaProducto = p.existenciaProducto - dp.cantidad
    WHERE dp.id_produccion = p_idProduccion;

    -- Eliminar detalles anteriores
    DELETE FROM DetalleProduccion WHERE id_produccion = p_idProduccion;

    -- Actualizar encabezado
    UPDATE ProductosProduccion
    SET fechaEntrada = p_fechaEntrada, observacion = p_observacion, id_usuario = p_idUsuario
    WHERE idProduccion = p_idProduccion;

    -- Procesar nuevos detalles
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_idProducto, v_cantidad, v_costo, v_idFabricante;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Validar producto en taller
        IF NOT EXISTS (SELECT 1 FROM Producto
        WHERE id_producto = v_idProducto AND idUbicacionPro = 1)THEN
            ROLLBACK;
            SET v_errorMsg = CONCAT('Producto ', v_idProducto, ' no existe en el taller.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Validar cantidad > 0
        IF v_cantidad <= 0 THEN
            ROLLBACK;
            SET v_errorMsg = CONCAT('Cantidad inválida para producto ', v_idProducto);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Validar costo > 0
        IF v_costo <= 0 THEN
            ROLLBACK;
            SET v_errorMsg = CONCAT('Costo inválido para producto ', v_idProducto);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Validar fabricante
        IF NOT EXISTS (SELECT 1 FROM Empleado WHERE idEmpleado = v_idFabricante)THEN
            ROLLBACK;
            SET v_errorMsg = CONCAT('Fabricante (Empleado) ', v_idFabricante, ' no existe.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_errorMsg;
        END IF;

        -- Insertar nuevo detalle
        INSERT INTO DetalleProduccion (id_produccion, id_producto, cantidad, costo_unitario, idFabricante)
        VALUES (p_idProduccion, v_idProducto, v_cantidad, v_costo, v_idFabricante);

        -- Aumentar nuevo stock
        UPDATE Producto
        SET existenciaProducto = existenciaProducto + v_cantidad
        WHERE id_producto = v_idProducto AND idUbicacionPro = 1;
    END LOOP;
    CLOSE cur;

    COMMIT;
END //
DELIMITER ;

/*PROCEDIMIENTO DAR DE BAJA REGISTRO*/
 
 DELIMITER //
CREATE PROCEDURE DarDeBajaProduccion(
    IN p_idProduccion INT
)
BEGIN
    -- Validar que exista y esté activa
    IF NOT EXISTS (SELECT 1
    FROM ProductosProduccion
    WHERE idProduccion = p_idProduccion AND EstadoRegistro = 1)THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Producción no encontrada o ya inactiva.';
    END IF;

    START TRANSACTION;

    -- Revertir el stock
    UPDATE Producto p
    JOIN DetalleProduccion dp ON p.id_producto = dp.id_producto AND p.idUbicacionPro = 1
    SET p.existenciaProducto = p.existenciaProducto - dp.cantidad
    WHERE dp.id_produccion = p_idProduccion;

    -- Marcar como inactiva
    UPDATE ProductosProduccion
    SET EstadoRegistro = 0
    WHERE idProduccion = p_idProduccion;

    COMMIT;
END //
DELIMITER ;