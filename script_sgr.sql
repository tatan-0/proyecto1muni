DROP DATABASE IF EXISTS sgr_laserena;
CREATE DATABASE sgr_laserena DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sgr_laserena;

CREATE TABLE DELEGACION (
    id_delegacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre_delegacion VARCHAR(100) NOT NULL UNIQUE,
    comuna VARCHAR(50) NOT NULL DEFAULT 'La Serena'
) ENGINE=InnoDB;

CREATE TABLE CARGO (
    id_cargo INT AUTO_INCREMENT PRIMARY KEY,
    nombre_cargo VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE USUARIO (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    rut VARCHAR(12) NOT NULL UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'Funcionario',
    id_delegacion INT NOT NULL,
    id_cargo INT NOT NULL,
    CONSTRAINT fk_usuario_delegacion FOREIGN KEY (id_delegacion) REFERENCES DELEGACION(id_delegacion) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_usuario_cargo FOREIGN KEY (id_cargo) REFERENCES CARGO(id_cargo) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ITEM_MEDICION (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    nombre_item VARCHAR(150) NOT NULL,
    ponderador DECIMAL(5,2) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE META (
    id_meta INT AUTO_INCREMENT PRIMARY KEY,
    cantidad_meta INT NOT NULL,
    trimestre INT NOT NULL,
    anio INT NOT NULL DEFAULT 2026,
    id_cargo INT NOT NULL,
    id_item INT NOT NULL,
    CONSTRAINT fk_meta_cargo FOREIGN KEY (id_cargo) REFERENCES CARGO(id_cargo) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_meta_item FOREIGN KEY (id_item) REFERENCES ITEM_MEDICION(id_item) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE ACTIVIDAD (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    descripcion_problema TEXT NOT NULL,
    accion_ejecutada TEXT NOT NULL,
    contacto_nombre VARCHAR(100),
    contacto_telefono VARCHAR(20),
    ingresa_tubo BOOLEAN DEFAULT FALSE,
    id_usuario INT NOT NULL,
    id_item INT NOT NULL,
    CONSTRAINT fk_actividad_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_actividad_item FOREIGN KEY (id_item) REFERENCES ITEM_MEDICION(id_item) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE EVIDENCIA (
    id_evidencia INT AUTO_INCREMENT PRIMARY KEY,
    codigo_unico VARCHAR(20) NOT NULL UNIQUE,
    ruta_foto VARCHAR(255),
    estado_validacion VARCHAR(20) DEFAULT 'Pendiente',
    observacion_verificador TEXT,
    id_actividad INT NOT NULL UNIQUE,
    CONSTRAINT fk_evidencia_actividad FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE COMPROMISO_TUBO (
    id_compromiso INT AUTO_INCREMENT PRIMARY KEY,
    fecha_solicitud DATE NOT NULL,
    solicitante VARCHAR(100),
    territorio VARCHAR(100),
    responsable VARCHAR(100),
    fecha_compromiso DATE,
    area_apoyo VARCHAR(100),
    estado_tubo VARCHAR(20) DEFAULT 'INGRESADO',
    id_actividad INT NULL,
    id_delegacion INT NOT NULL,
    CONSTRAINT fk_tubo_actividad FOREIGN KEY (id_actividad) REFERENCES ACTIVIDAD(id_actividad) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_tubo_delegacion FOREIGN KEY (id_delegacion) REFERENCES DELEGACION(id_delegacion) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

INSERT INTO DELEGACION (nombre_delegacion) VALUES 
('Rural'), 
('Centro'), 
('Avenida del Mar'), 
('La Antena - La Florida'), 
('Las Compañías'), 
('La Pampa');

INSERT INTO CARGO (nombre_cargo) VALUES 
('Territorial OO.CC.'), 
('Delegado Municipal'), 
('Verificador de Campo'), 
('Administrador del Sistema');