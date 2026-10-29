-- =====================================================================
-- Tech Solutions - Professional Services Management System
-- Target: MySQL 8.0.16+ / MariaDB 10.2+ (InnoDB, utf8mb4)
--
-- Portability notes:
--   * Every FK uses ON UPDATE RESTRICT instead of ON UPDATE CASCADE.
--     MariaDB rejects (error 1901) any CHECK constraint that references
--     a column belonging to a FK declared with ON UPDATE CASCADE.
--     All primary keys are AUTO_INCREMENT and never change, so
--     RESTRICT behaves exactly the same in practice and runs on both
--     engines.
--   * CHECK constraints are enforced from MySQL 8.0.16 and MariaDB
--     10.2 onwards. On older servers they are parsed but ignored.
--   * JSON columns require MySQL 5.7+ / MariaDB 10.2+.
--
-- Conventions: snake_case, plural table names, `id` as primary key,
-- `<table_singular>_id` as foreign key, explicit constraint/index names.
--
-- Tables marked [DER] come from the entity-relationship diagram.
-- Tables/columns marked [ADDED] are required by the rest of the analysis
-- (use cases, requirements, integrations) and are NOT in the DER.
--
-- Run with DBeaver: Alt+X (Execute SQL Script) and check the log at the
-- end. DBeaver keeps executing after a statement fails, so a silent
-- error can leave the schema half-created.
-- =====================================================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS tech_solutions
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE tech_solutions;

-- Shows in the execution log which engine actually ran the script.
SELECT VERSION() AS motor, @@version_comment AS build;

-- ---------------------------------------------------------------------
-- Clean start (reverse dependency order)
-- FOREIGN_KEY_CHECKS is disabled so a wrong drop order cannot fail.
-- ---------------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS integration_audit_logs;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS claims;
DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS plan_change_requests;
DROP TABLE IF EXISTS service_requests;
DROP TABLE IF EXISTS client_services;
DROP TABLE IF EXISTS administrators;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS priorities;
DROP TABLE IF EXISTS request_statuses;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS plans;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- [ADDED] users: authentication (login, registration, role)
-- ---------------------------------------------------------------------
CREATE TABLE users (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  email          VARCHAR(255) NOT NULL,
  password_hash  VARCHAR(255) NOT NULL,
  role           ENUM('client', 'admin') NOT NULL,
  is_active      TINYINT(1) NOT NULL DEFAULT 1,
  last_login_at  DATETIME NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] plans  (plan_id, nombre_plan, descripcion, monto)
-- ---------------------------------------------------------------------
CREATE TABLE plans (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name         VARCHAR(100) NOT NULL,
  description  VARCHAR(500) NULL,
  price        DECIMAL(12,2) NOT NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_plans_name (name),
  CONSTRAINT chk_plans_price CHECK (price >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] services  (servicio_id, nombre_servicio, descripcion)
-- ---------------------------------------------------------------------
CREATE TABLE services (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name         VARCHAR(150) NOT NULL,
  description  VARCHAR(500) NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_services_name (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] request_statuses  (estado_id, descripcion)  -- catalog
-- ---------------------------------------------------------------------
CREATE TABLE request_statuses (
  id           TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name         VARCHAR(30) NOT NULL,
  description  VARCHAR(100) NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_request_statuses_name (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] priorities  (prioridad_id, descripcion)  -- catalog
-- ---------------------------------------------------------------------
CREATE TABLE priorities (
  id           TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  name         VARCHAR(30) NOT NULL,
  description  VARCHAR(100) NULL,
  level        TINYINT UNSIGNED NOT NULL COMMENT '1 = most urgent',
  PRIMARY KEY (id),
  UNIQUE KEY uq_priorities_name (name)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] clients  (cliente_id, nombre, email, telefono)
--       + relationship "es contratado por": each client has one plan (N:1)
-- ---------------------------------------------------------------------
CREATE TABLE clients (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id      INT UNSIGNED NULL COMMENT 'NULL until the client gets login access',
  plan_id      INT UNSIGNED NOT NULL,
  name         VARCHAR(150) NOT NULL,
  email        VARCHAR(255) NOT NULL,
  phone        VARCHAR(30) NULL,
  dni          VARCHAR(20) NULL COMMENT '[ADDED] DNI, digits only, used by VeriCheck',
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_clients_user_id (user_id),
  UNIQUE KEY uq_clients_email (email),
  UNIQUE KEY uq_clients_dni (dni),
  KEY idx_clients_plan_id (plan_id),
  CONSTRAINT fk_clients_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT fk_clients_plan FOREIGN KEY (plan_id)
    REFERENCES plans (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] administrators  (administrador_id, nombre)
-- ---------------------------------------------------------------------
CREATE TABLE administrators (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED NOT NULL,
  name        VARCHAR(150) NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_administrators_user_id (user_id),
  CONSTRAINT fk_administrators_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] client_services: N:M relationship "modifica" between Cliente
-- and Servicio. Used as the list of services a client has contracted.
-- ---------------------------------------------------------------------
CREATE TABLE client_services (
  client_id     INT UNSIGNED NOT NULL,
  service_id    INT UNSIGNED NOT NULL,
  contracted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (client_id, service_id),
  KEY idx_client_services_service_id (service_id),
  CONSTRAINT fk_client_services_client FOREIGN KEY (client_id)
    REFERENCES clients (id) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT fk_client_services_service FOREIGN KEY (service_id)
    REFERENCES services (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] service_requests  (solicitud_id, tipo_modificacion)
--   Relationships: N:1 status, N:1 service, N:1 priority, N:1 administrator
--   [ADDED] client_id: the DER does not link requests to clients, but the
--   data dictionary requires it. The composite FK guarantees a client can
--   only request changes on a service they actually contracted (CU2).
-- ---------------------------------------------------------------------
CREATE TABLE service_requests (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id         INT UNSIGNED NOT NULL,
  service_id        INT UNSIGNED NOT NULL,
  status_id         TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1 = pending',
  priority_id       TINYINT UNSIGNED NULL COMMENT 'assigned later by an administrator',
  administrator_id  INT UNSIGNED NULL COMMENT 'administrator in charge',
  modification_type VARCHAR(100) NOT NULL,
  description       TEXT NULL,
  rejection_reason  VARCHAR(500) NULL,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  resolved_at       DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_service_requests_client (client_id, created_at),
  KEY idx_service_requests_service (service_id),
  KEY idx_service_requests_status_priority (status_id, priority_id),
  KEY idx_service_requests_administrator (administrator_id),
  CONSTRAINT fk_service_requests_client_service FOREIGN KEY (client_id, service_id)
    REFERENCES client_services (client_id, service_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_service_requests_status FOREIGN KEY (status_id)
    REFERENCES request_statuses (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_service_requests_priority FOREIGN KEY (priority_id)
    REFERENCES priorities (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_service_requests_administrator FOREIGN KEY (administrator_id)
    REFERENCES administrators (id) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [ADDED] plan_change_requests: plan upgrade/downgrade flow (CU9, CU15)
-- ---------------------------------------------------------------------
CREATE TABLE plan_change_requests (
  id                 INT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id          INT UNSIGNED NOT NULL,
  current_plan_id    INT UNSIGNED NOT NULL,
  requested_plan_id  INT UNSIGNED NOT NULL,
  status_id          TINYINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '1 = pending',
  administrator_id   INT UNSIGNED NULL,
  reason             VARCHAR(500) NULL,
  identity_verified  TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'VeriCheck result',
  created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at        DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_plan_change_requests_client (client_id),
  KEY idx_plan_change_requests_current_plan (current_plan_id),
  KEY idx_plan_change_requests_requested_plan (requested_plan_id),
  KEY idx_plan_change_requests_status (status_id),
  KEY idx_plan_change_requests_administrator (administrator_id),
  CONSTRAINT chk_plan_change_requests_plans CHECK (current_plan_id <> requested_plan_id),
  -- ON UPDATE RESTRICT (not CASCADE): MariaDB rejects the CHECK above
  -- when it references a column of a FK with ON UPDATE CASCADE.
  CONSTRAINT fk_plan_change_requests_client FOREIGN KEY (client_id)
    REFERENCES clients (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_plan_change_requests_current_plan FOREIGN KEY (current_plan_id)
    REFERENCES plans (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_plan_change_requests_requested_plan FOREIGN KEY (requested_plan_id)
    REFERENCES plans (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_plan_change_requests_status FOREIGN KEY (status_id)
    REFERENCES request_statuses (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_plan_change_requests_administrator FOREIGN KEY (administrator_id)
    REFERENCES administrators (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [ADDED] attachments: documents/images linked to a request (CU4)
-- ---------------------------------------------------------------------
CREATE TABLE attachments (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  request_id   INT UNSIGNED NOT NULL,
  file_name    VARCHAR(255) NOT NULL,
  file_path    VARCHAR(500) NOT NULL,
  file_type    VARCHAR(100) NOT NULL COMMENT 'MIME type',
  uploaded_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_attachments_request_id (request_id),
  CONSTRAINT fk_attachments_request FOREIGN KEY (request_id)
    REFERENCES service_requests (id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] claims  (reclamo_id, estado, descripcion, categoria, fecha)
--       + relationship "realiza": Cliente 1:N Reclamo
--   [ADDED] service_id (CU8 picks the service), priority_id (initial
--   priority), administrator_id (assignee, used by the claims report).
-- ---------------------------------------------------------------------
CREATE TABLE claims (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id         INT UNSIGNED NOT NULL,
  service_id        INT UNSIGNED NULL,
  priority_id       TINYINT UNSIGNED NULL,
  administrator_id  INT UNSIGNED NULL,
  category          ENUM('technical', 'support', 'service', 'other') NOT NULL DEFAULT 'other',
  description       TEXT NOT NULL,
  status            ENUM('pending', 'resolved', 'closed') NOT NULL DEFAULT 'pending',
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at       DATETIME NULL,
  PRIMARY KEY (id),
  KEY idx_claims_client (client_id, created_at),
  KEY idx_claims_status (status),
  KEY idx_claims_priority (priority_id),
  KEY idx_claims_administrator (administrator_id),
  CONSTRAINT fk_claims_client_service FOREIGN KEY (client_id, service_id)
    REFERENCES client_services (client_id, service_id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_claims_client FOREIGN KEY (client_id)
    REFERENCES clients (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_claims_priority FOREIGN KEY (priority_id)
    REFERENCES priorities (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_claims_administrator FOREIGN KEY (administrator_id)
    REFERENCES administrators (id) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [DER] invoices  (factura_id, monto, fecha)
--       + "tiene": Cliente 1:N Factura, "contrata": Factura N:1 Plan
--   [ADDED] sync_status / sent_at: PagoNet delivery state, so failed
--   sends can be retried (CU15 "pending retry").
-- ---------------------------------------------------------------------
CREATE TABLE invoices (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  client_id    INT UNSIGNED NOT NULL,
  plan_id      INT UNSIGNED NOT NULL,
  amount       DECIMAL(12,2) NOT NULL,
  issued_at    DATE NOT NULL,
  sync_status  ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
  sent_at      DATETIME NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_invoices_client (client_id, issued_at),
  KEY idx_invoices_plan (plan_id),
  KEY idx_invoices_sync_status (sync_status),
  CONSTRAINT chk_invoices_amount CHECK (amount >= 0),
  CONSTRAINT fk_invoices_client FOREIGN KEY (client_id)
    REFERENCES clients (id) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_invoices_plan FOREIGN KEY (plan_id)
    REFERENCES plans (id) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [ADDED] integration_audit_logs: every send/response/error with
-- external systems (RF-20, RNF-07). Supports retries.
-- ---------------------------------------------------------------------
CREATE TABLE integration_audit_logs (
  id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  system_name      VARCHAR(30) NOT NULL COMMENT 'PagoNet, CRMMax, NotiSys, AnalytixPro, VeriCheck, WhatsApp, API',
  direction        ENUM('outbound', 'inbound') NOT NULL,
  http_method      VARCHAR(10) NULL,
  endpoint         VARCHAR(500) NULL,
  request_payload  JSON NULL,
  response_status  SMALLINT UNSIGNED NULL,
  response_body    JSON NULL,
  status           ENUM('success', 'failed', 'retry_pending') NOT NULL,
  error_message    VARCHAR(1000) NULL,
  retry_count      TINYINT UNSIGNED NOT NULL DEFAULT 0,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_integration_audit_logs_system_date (system_name, created_at),
  KEY idx_integration_audit_logs_status (status)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- [ADDED] notifications: in-app inbox (bell + unread counter).
--   One row per recipient. `is_read` is flipped when the user opens the
--   inbox. Outbound email/SMS delivery is not tracked here: that is a
--   technical trace and belongs to integration_audit_logs.
-- ---------------------------------------------------------------------
CREATE TABLE notifications (
  id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id     INT UNSIGNED NOT NULL,
  message     VARCHAR(500) NOT NULL,
  is_read     TINYINT(1) NOT NULL DEFAULT 0,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_notifications_user (user_id, is_read),
  CONSTRAINT fk_notifications_user FOREIGN KEY (user_id)
    REFERENCES users (id) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Seed data (catalogs). Fixed ids so the application can rely on them.
-- ---------------------------------------------------------------------
-- Status names follow the data dictionary and the client's wording:
-- 1 = pending, 5 = completed ("realizado").
INSERT INTO request_statuses (id, name, description) VALUES
  (1, 'pendiente',   'Solicitud creada y pendiente de atención'),
  (2, 'en_revision', 'Un administrador está analizando la solicitud'),
  (3, 'aprobado',    'Solicitud aprobada'),
  (4, 'rechazado',   'Solicitud rechazada'),
  (5, 'realizado',   'Solicitud atendida y resuelta');

INSERT INTO priorities (id, name, description, level) VALUES
  (1, 'alta',  'Atender primero', 1),
  (2, 'media', 'Atención normal', 2),
  (3, 'baja',  'Atender cuando haya capacidad', 3);

-- Service catalog taken from the case study ("Catálogo de Servicio de Consultores").
INSERT INTO services (name, description) VALUES
  ('Consultoría en Finanzas y Contabilidad',      'Asesoría en gestión financiera y tributaria'),
  ('Consultoría en Marketing Digital',            'Diseño de estrategias de publicidad y posicionamiento en redes sociales'),
  ('Consultoría en Recursos Humanos y Talento',   'Selección y capacitación de personal'),
  ('Consultoría en Desarrollo Web y UX/UI',       'Diseño y optimización de plataformas digitales'),
  ('Consultoría en Logística y Cadena de Suministro', 'Gestión de inventario y distribución'),
  ('Consultoría en Inteligencia Artificial y Machine Learning', 'Implementación de soluciones de IA para automatizar procesos'),
  ('Consultoría en Gestión de Proyectos Agile',   'Capacitación y soporte en metodologías ágiles'),
  ('Consultoría en Cumplimiento Legal y Normativo', 'Asesoría en normativas legales específicas de cada sector');

-- Plans are required before any client can be created: clients.plan_id is
-- NOT NULL. Prices follow the billing example of the case study.
INSERT INTO plans (name, description, price) VALUES
  ('Básico',      'Atención estándar, 1 servicio activo',     3500.00),
  ('Profesional', 'Atención prioritaria, hasta 3 servicios',  5900.00),
  ('Premium',     'Atención inmediata, servicios ilimitados', 7900.00);

-- ---------------------------------------------------------------------
-- Sanity check: expected row counts after a clean run.
-- ---------------------------------------------------------------------
SELECT 'request_statuses' AS tabla, COUNT(*) AS filas FROM request_statuses
UNION ALL SELECT 'priorities', COUNT(*) FROM priorities
UNION ALL SELECT 'services',   COUNT(*) FROM services
UNION ALL SELECT 'plans',      COUNT(*) FROM plans;