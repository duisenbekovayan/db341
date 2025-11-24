-- Database Schema for Online Caregivers Platform
-- Part 1: Physical Database Construction

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS appointment CASCADE;
DROP TABLE IF EXISTS job_application CASCADE;
DROP TABLE IF EXISTS job CASCADE;
DROP TABLE IF EXISTS address CASCADE;
DROP TABLE IF EXISTS caregiver CASCADE;
DROP TABLE IF EXISTS member CASCADE;
DROP TABLE IF EXISTS "user" CASCADE;

-- Create USER table
CREATE TABLE "user" (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    given_name VARCHAR(100) NOT NULL,
    surname VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    profile_description TEXT,
    password VARCHAR(255) NOT NULL
);

-- Create CAREGIVER table
CREATE TABLE caregiver (
    caregiver_user_id INTEGER PRIMARY KEY,
    photo VARCHAR(500),
    gender VARCHAR(20) NOT NULL,
    caregiving_type VARCHAR(50) NOT NULL CHECK (caregiving_type IN ('babysitter', 'elderly care', 'playmate')),
    hourly_rate DECIMAL(10, 2) NOT NULL CHECK (hourly_rate > 0),
    FOREIGN KEY (caregiver_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);

-- Create MEMBER table
CREATE TABLE member (
    member_user_id INTEGER PRIMARY KEY,
    house_rules TEXT,
    dependent_description TEXT,
    FOREIGN KEY (member_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
);

-- Create ADDRESS table
CREATE TABLE address (
    member_user_id INTEGER PRIMARY KEY,
    house_number VARCHAR(20) NOT NULL,
    street VARCHAR(200) NOT NULL,
    town VARCHAR(100) NOT NULL,
    FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
);

-- Create JOB table
CREATE TABLE job (
    job_id SERIAL PRIMARY KEY,
    member_user_id INTEGER NOT NULL,
    required_caregiving_type VARCHAR(50) NOT NULL CHECK (required_caregiving_type IN ('babysitter', 'elderly care', 'playmate')),
    other_requirements TEXT,
    date_posted DATE NOT NULL DEFAULT CURRENT_DATE,
    FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
);

-- Create JOB_APPLICATION table
CREATE TABLE job_application (
    caregiver_user_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    date_applied DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (caregiver_user_id, job_id),
    FOREIGN KEY (caregiver_user_id) REFERENCES caregiver(caregiver_user_id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job(job_id) ON DELETE CASCADE
);

-- Create APPOINTMENT table
CREATE TABLE appointment (
    appointment_id SERIAL PRIMARY KEY,
    caregiver_user_id INTEGER NOT NULL,
    member_user_id INTEGER NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    work_hours DECIMAL(4, 2) NOT NULL CHECK (work_hours > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'declined')),
    FOREIGN KEY (caregiver_user_id) REFERENCES caregiver(caregiver_user_id) ON DELETE CASCADE,
    FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_caregiver_type ON caregiver(caregiving_type);
CREATE INDEX idx_job_type ON job(required_caregiving_type);
CREATE INDEX idx_appointment_status ON appointment(status);
CREATE INDEX idx_appointment_date ON appointment(appointment_date);
CREATE INDEX idx_user_city ON "user"(city);

