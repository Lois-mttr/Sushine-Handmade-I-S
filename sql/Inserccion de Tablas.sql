use nexodb
-- INSERCCION TABLA CATEGORIA
INSERT INTO Categoria (nombreCategoria, descripcionCategoria, estadoCategoria) 
VALUES 
('Carteras', 'Estuche pequeño de cuero, que se pliega por la mitad apta para el bolsillo', 1),
('Bolsos', ' Accesorio versátil de mano y funcional utilizado para transportar objetos personales', 1),
('Mochilas', 'bolsa de cuero, tela y lona provista de correas que permiten llevarla en la espalda', 1);

-- INSERCCION TABLA UBICACION
Insert into Ubicacion (nombreUbicacion, direccion) values 
('Taller',' Sunshine Handmade Taller, Km. 20, 3 Carr. a Masaya, Los Madrigales' ), 
('Sucursal','Sunshine Handmade, Centro Comercial Galerías, Pista Jean Paul Genie, Managua');
-- INSERCCION TABLA PRODUCTO
INSERT INTO Producto (id_producto, idUbicacionPro, nombreProducto, descripcionProducto, existenciaProducto, imagenProductoRuta, idCategoriaPro, precioProducto, estado, existenciaMinima)
VALUES 
('PROD001', 1, 'Bolso Cuero', 'bolso hecho a mano con tela canvaa', 10, NULL, 2, 29.79, 1, 5),
('PROD001', 2, 'Bolso Cuero', 'bolso hecho a mano con tela canvaa', 25, NULL, 2, 29.79, 1, 5),
('PROD002', 1, 'Billetera Zure', 'billetera de color co ziper', 15, NULL, 3, 79.99, 1, 5),
('PROD002', 2, 'Billetera Zure', 'billetera de color co ziper', 8, NULL, 3, 79.99, 1, 5);
-- INSERCCION TABLA PERSONA
INSERT INTO Persona (cedula, primerNombre, segundoNombre, primerApellido, segundoApellido, direccion, estadoPersona)
VALUES 
('123-456789-0001X', 'Campary', NULL, 'Ramirez', NULL, 'Carretera Masaya Nic.', 1),
('421-456789-00x1X', 'María', NULL, 'Fernández', 'Ruiz', 'Calle 5, Masaya', 1),
('0056789012345678', 'Luis', NULL, 'Ramírez', 'Castillo', 'Residencial Altamira, Estelí', 1),
('0012789012345678', 'Juan', 'Carlos', 'González', 'Martínez', 'Av. Central #123, Managua', 1),
('0034567890123456', 'Pedro', 'José', 'Rodríguez', NULL, 'Colonia Los Robles, Granada', 1),
('0045678901234567', 'Ana', 'Lucía', 'Mendoza', 'Torres', 'Barrio San Antonio, León', 1);

-- INSERCCION TABLA CLIENTE
INSERT INTO Cliente (correo, idPersonaCliente, estadoCliente)
VALUES 
('juan.gonzalez@email.com', '0012789012345678', 1),
('maria.fernandez@email.com', '0045678901234567', 1);
-- INSERCCION TABLA EMPLEADO
INSERT INTO Empleado (rolEmpleado, fechaContratacion, salario, correo, idPersonaEmp, estadoEmpleado)
VALUES 
('Gerente', '2025-05-01 09:00:00', 2500.00, 'camparyramirez@gmail.com', '123-456789-0001X', 1),
('Responsable Sucursal', '2024-11-15 08:30:00', 1500.00, 'mariafernandez@gmail.com', '421-456789-00x1X', 1),
('Obrero', '2025-05-01 09:00:00', 2000.00, 'lui.ramirez@gmail.com', '0056789012345678', 1);

