CREATE DATABASE IF NOT EXISTS smart_recruitment
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_recruitment;

CREATE TABLE IF NOT EXISTS sys_department (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  code VARCHAR(64) NOT NULL UNIQUE,
  parent_id BIGINT NULL,
  description VARCHAR(500) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_department_parent (parent_id),
  CONSTRAINT fk_department_parent FOREIGN KEY (parent_id) REFERENCES sys_department(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_user (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  real_name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NULL UNIQUE,
  phone VARCHAR(32) NULL UNIQUE,
  department_id BIGINT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  last_login_at DATETIME(6) NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_user_department (department_id),
  KEY idx_user_status (status),
  CONSTRAINT fk_user_department FOREIGN KEY (department_id) REFERENCES sys_department(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  code VARCHAR(64) NOT NULL UNIQUE,
  description VARCHAR(500) NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_user_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL,
  UNIQUE KEY uq_user_role (user_id, role_id),
  CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES sys_role(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_permission (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  code VARCHAR(100) NOT NULL UNIQUE,
  resource VARCHAR(100) NOT NULL,
  action VARCHAR(50) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sys_role_permission (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  role_id BIGINT NOT NULL,
  permission_id BIGINT NOT NULL,
  created_at DATETIME(6) NOT NULL,
  UNIQUE KEY uq_role_permission (role_id, permission_id),
  CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES sys_role(id) ON DELETE CASCADE,
  CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES sys_permission(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS job_category (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  code VARCHAR(64) NOT NULL UNIQUE,
  parent_id BIGINT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT fk_category_parent FOREIGN KEY (parent_id) REFERENCES job_category(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS job_position (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(200) NOT NULL,
  code VARCHAR(64) NOT NULL UNIQUE,
  category_id BIGINT NULL,
  department_id BIGINT NULL,
  recruiter_id BIGINT NULL,
  description TEXT NOT NULL,
  requirements TEXT NOT NULL,
  skills JSON NOT NULL,
  location VARCHAR(200) NULL,
  employment_type VARCHAR(50) NOT NULL DEFAULT 'FULL_TIME',
  salary_min DOUBLE NULL,
  salary_max DOUBLE NULL,
  headcount INT NOT NULL DEFAULT 1,
  status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
  published_at DATETIME(6) NULL,
  closed_at DATETIME(6) NULL,
  created_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_job_status (status),
  KEY idx_job_title (title),
  CONSTRAINT fk_job_category FOREIGN KEY (category_id) REFERENCES job_category(id),
  CONSTRAINT fk_job_department FOREIGN KEY (department_id) REFERENCES sys_department(id),
  CONSTRAINT fk_job_recruiter FOREIGN KEY (recruiter_id) REFERENCES sys_user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS candidate (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NULL,
  phone VARCHAR(32) NULL,
  gender VARCHAR(20) NULL,
  birth_date DATE NULL,
  education VARCHAR(100) NULL,
  work_years DOUBLE NULL,
  current_company VARCHAR(200) NULL,
  current_title VARCHAR(200) NULL,
  skills JSON NOT NULL,
  summary TEXT NULL,
  source VARCHAR(100) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  created_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_candidate_name (name),
  KEY idx_candidate_status (status),
  CONSTRAINT fk_candidate_creator FOREIGN KEY (created_by) REFERENCES sys_user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS resume (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  candidate_id BIGINT NULL,
  filename VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_hash CHAR(64) NOT NULL UNIQUE,
  file_type VARCHAR(20) NOT NULL,
  file_size INT NOT NULL,
  raw_text LONGTEXT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'UPLOADED',
  uploaded_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_resume_candidate (candidate_id),
  KEY idx_resume_status (status),
  CONSTRAINT fk_resume_candidate FOREIGN KEY (candidate_id) REFERENCES candidate(id),
  CONSTRAINT fk_resume_uploader FOREIGN KEY (uploaded_by) REFERENCES sys_user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ai_task (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_no VARCHAR(64) NOT NULL UNIQUE,
  task_type VARCHAR(50) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  provider VARCHAR(50) NOT NULL DEFAULT 'local',
  model_name VARCHAR(100) NULL,
  input_payload JSON NOT NULL,
  output_payload JSON NULL,
  error_message TEXT NULL,
  degraded TINYINT(1) NOT NULL DEFAULT 0,
  started_at DATETIME(6) NULL,
  finished_at DATETIME(6) NULL,
  created_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_ai_task_type_status (task_type, status),
  CONSTRAINT fk_ai_task_creator FOREIGN KEY (created_by) REFERENCES sys_user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ai_chat_session (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_no VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  title VARCHAR(200) NOT NULL,
  job_id BIGINT NULL,
  candidate_id BIGINT NULL,
  resume_id BIGINT NULL,
  message_count INT NOT NULL DEFAULT 0,
  last_message_preview VARCHAR(500) NULL,
  last_message_at DATETIME(6) NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  deleted_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY uq_ai_chat_session_no (session_no),
  KEY idx_ai_chat_session_user (user_id),
  KEY idx_ai_chat_session_job (job_id),
  KEY idx_ai_chat_session_candidate (candidate_id),
  KEY idx_ai_chat_session_resume (resume_id),
  KEY idx_ai_chat_session_deleted (is_deleted),
  CONSTRAINT fk_ai_chat_session_user FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
  CONSTRAINT fk_ai_chat_session_job FOREIGN KEY (job_id) REFERENCES job_position(id) ON DELETE SET NULL,
  CONSTRAINT fk_ai_chat_session_candidate FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE SET NULL,
  CONSTRAINT fk_ai_chat_session_resume FOREIGN KEY (resume_id) REFERENCES resume(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ai_chat_message (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  message_no VARCHAR(64) NOT NULL,
  session_id BIGINT NOT NULL,
  user_id BIGINT NULL,
  role VARCHAR(20) NOT NULL,
  status VARCHAR(20) NOT NULL,
  sequence_no INT NOT NULL,
  content LONGTEXT NOT NULL,
  citations JSON NOT NULL,
  context_snapshot JSON NOT NULL,
  provider VARCHAR(50) NOT NULL DEFAULT 'local',
  model_name VARCHAR(100) NULL,
  latency_ms DOUBLE NULL,
  error_message LONGTEXT NULL,
  idempotency_key VARCHAR(128) NULL,
  retry_of_message_id BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY uq_ai_chat_message_no (message_no),
  UNIQUE KEY uq_ai_chat_message_session_sequence (session_id, sequence_no),
  KEY idx_ai_chat_message_session (session_id),
  KEY idx_ai_chat_message_user (user_id),
  KEY idx_ai_chat_message_role (role),
  KEY idx_ai_chat_message_status (status),
  KEY idx_ai_chat_message_idempotency (idempotency_key),
  KEY idx_ai_chat_message_retry_of (retry_of_message_id),
  CONSTRAINT fk_ai_chat_message_session FOREIGN KEY (session_id) REFERENCES ai_chat_session(id) ON DELETE CASCADE,
  CONSTRAINT fk_ai_chat_message_user FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE SET NULL,
  CONSTRAINT fk_ai_chat_message_retry_of FOREIGN KEY (retry_of_message_id) REFERENCES ai_chat_message(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS resume_parse_record (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  resume_id BIGINT NOT NULL,
  task_id BIGINT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'PARSED',
  parsed_data JSON NOT NULL,
  confidence DOUBLE NOT NULL DEFAULT 0,
  confirmed_by BIGINT NULL,
  confirmed_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_parse_resume (resume_id),
  CONSTRAINT fk_parse_resume FOREIGN KEY (resume_id) REFERENCES resume(id) ON DELETE CASCADE,
  CONSTRAINT fk_parse_task FOREIGN KEY (task_id) REFERENCES ai_task(id),
  CONSTRAINT fk_parse_confirmer FOREIGN KEY (confirmed_by) REFERENCES sys_user(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS job_application (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  job_id BIGINT NOT NULL,
  candidate_id BIGINT NOT NULL,
  resume_id BIGINT NULL,
  stage VARCHAR(30) NOT NULL DEFAULT 'APPLIED',
  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  source VARCHAR(100) NULL,
  applied_at DATETIME(6) NOT NULL,
  updated_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY uq_job_candidate_application (job_id, candidate_id),
  KEY idx_application_stage (stage),
  CONSTRAINT fk_application_job FOREIGN KEY (job_id) REFERENCES job_position(id) ON DELETE CASCADE,
  CONSTRAINT fk_application_candidate FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE,
  CONSTRAINT fk_application_resume FOREIGN KEY (resume_id) REFERENCES resume(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vector_document (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  source_type VARCHAR(50) NOT NULL,
  source_id BIGINT NOT NULL,
  content LONGTEXT NOT NULL,
  embedding JSON NOT NULL,
  extra_data JSON NOT NULL,
  algorithm_version VARCHAR(50) NOT NULL,
  content_hash CHAR(64) NOT NULL UNIQUE,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_vector_source (source_type, source_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS job_match_result (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  job_id BIGINT NOT NULL,
  candidate_id BIGINT NOT NULL,
  application_id BIGINT NULL,
  score DOUBLE NOT NULL,
  rule_score DOUBLE NOT NULL DEFAULT 0,
  vector_score DOUBLE NULL,
  llm_score DOUBLE NULL,
  level VARCHAR(20) NOT NULL,
  reasons JSON NOT NULL,
  detail JSON NOT NULL,
  algorithm_version VARCHAR(50) NOT NULL,
  prompt_version VARCHAR(50) NOT NULL,
  degraded TINYINT(1) NOT NULL DEFAULT 0,
  created_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_match_job_score (job_id, score),
  KEY idx_match_candidate (candidate_id),
  CONSTRAINT fk_match_job FOREIGN KEY (job_id) REFERENCES job_position(id) ON DELETE CASCADE,
  CONSTRAINT fk_match_candidate FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE,
  CONSTRAINT fk_match_application FOREIGN KEY (application_id) REFERENCES job_application(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interview_schedule (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  job_id BIGINT NOT NULL,
  candidate_id BIGINT NOT NULL,
  application_id BIGINT NULL,
  interviewer_id BIGINT NULL,
  title VARCHAR(200) NOT NULL,
  round_no INT NOT NULL DEFAULT 1,
  mode VARCHAR(30) NOT NULL DEFAULT 'OFFLINE',
  scheduled_at DATETIME(6) NOT NULL,
  duration_minutes INT NOT NULL DEFAULT 60,
  location VARCHAR(255) NULL,
  meeting_url VARCHAR(500) NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
  created_by BIGINT NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_interview_status_time (status, scheduled_at),
  CONSTRAINT fk_interview_job FOREIGN KEY (job_id) REFERENCES job_position(id) ON DELETE CASCADE,
  CONSTRAINT fk_interview_candidate FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE,
  CONSTRAINT fk_interview_application FOREIGN KEY (application_id) REFERENCES job_application(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interview_participant (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  interview_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  participant_role VARCHAR(30) NOT NULL DEFAULT 'INTERVIEWER',
  feedback TEXT NULL,
  score DOUBLE NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'INVITED',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  UNIQUE KEY uq_interview_participant (interview_id, user_id),
  CONSTRAINT fk_participant_interview FOREIGN KEY (interview_id) REFERENCES interview_schedule(id) ON DELETE CASCADE,
  CONSTRAINT fk_participant_user FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS interview_question (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  interview_id BIGINT NULL,
  job_id BIGINT NOT NULL,
  candidate_id BIGINT NULL,
  question TEXT NOT NULL,
  category VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
  reference_answer TEXT NULL,
  score_weight DOUBLE NOT NULL DEFAULT 1,
  status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
  generated_by VARCHAR(50) NOT NULL DEFAULT 'AI',
  approved_by BIGINT NULL,
  approved_at DATETIME(6) NULL,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  KEY idx_question_interview_status (interview_id, status),
  CONSTRAINT fk_question_interview FOREIGN KEY (interview_id) REFERENCES interview_schedule(id) ON DELETE CASCADE,
  CONSTRAINT fk_question_job FOREIGN KEY (job_id) REFERENCES job_position(id) ON DELETE CASCADE,
  CONSTRAINT fk_question_candidate FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS operation_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NULL,
  username VARCHAR(64) NULL,
  method VARCHAR(10) NOT NULL,
  path VARCHAR(500) NOT NULL,
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(100) NULL,
  resource_id VARCHAR(64) NULL,
  status_code INT NOT NULL DEFAULT 200,
  ip VARCHAR(64) NULL,
  user_agent VARCHAR(500) NULL,
  request_id VARCHAR(64) NULL,
  detail JSON NOT NULL,
  duration_ms DOUBLE NULL,
  created_at DATETIME(6) NOT NULL,
  KEY idx_operation_user_action (user_id, action),
  KEY idx_operation_request (request_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ai_execution_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id BIGINT NULL,
  provider VARCHAR(50) NOT NULL,
  model_name VARCHAR(100) NULL,
  prompt_version VARCHAR(50) NOT NULL,
  algorithm_version VARCHAR(50) NOT NULL,
  success TINYINT(1) NOT NULL DEFAULT 0,
  degraded TINYINT(1) NOT NULL DEFAULT 1,
  latency_ms DOUBLE NOT NULL DEFAULT 0,
  input_tokens INT NULL,
  output_tokens INT NULL,
  error_message TEXT NULL,
  input_digest CHAR(64) NULL,
  output_digest CHAR(64) NULL,
  created_at DATETIME(6) NOT NULL,
  KEY idx_ai_log_task (task_id),
  CONSTRAINT fk_ai_log_task FOREIGN KEY (task_id) REFERENCES ai_task(id)
) ENGINE=InnoDB;
