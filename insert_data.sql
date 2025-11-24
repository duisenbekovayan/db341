-- Sample Data Insertion
-- At least 10 instances for each table

-- Insert Users (need at least 20: 10 caregivers + 10 members)
INSERT INTO "user" (email, given_name, surname, city, phone_number, profile_description, password) VALUES
-- Caregivers
('sarah.johnson@email.com', 'Sarah', 'Johnson', 'Astana', '+1234567890', 'Experienced babysitter with 5 years of experience', 'pass123'),
('michael.chen@email.com', 'Michael', 'Chen', 'Almaty', '+1234567891', 'Professional elderly care specialist', 'pass123'),
('emily.davis@email.com', 'Emily', 'Davis', 'Astana', '+1234567892', 'Creative playmate for children', 'pass123'),
('david.wilson@email.com', 'David', 'Wilson', 'Shymkent', '+1234567893', 'Certified babysitter with first aid training', 'pass123'),
('lisa.anderson@email.com', 'Lisa', 'Anderson', 'Astana', '+1234567894', 'Compassionate elderly caregiver', 'pass123'),
('james.brown@email.com', 'James', 'Brown', 'Almaty', '+1234567895', 'Fun and energetic playmate', 'pass123'),
('maria.garcia@email.com', 'Maria', 'Garcia', 'Astana', '+1234567896', 'Experienced with special needs children', 'pass123'),
('robert.martinez@email.com', 'Robert', 'Martinez', 'Karaganda', '+1234567897', 'Professional elderly care with medical background', 'pass123'),
('jennifer.taylor@email.com', 'Jennifer', 'Taylor', 'Astana', '+1234567898', 'Creative activities for children', 'pass123'),
('william.thomas@email.com', 'William', 'Thomas', 'Almaty', '+1234567899', 'Reliable babysitter available weekends', 'pass123'),
-- Members
('arman.armanov@email.com', 'Arman', 'Armanov', 'Astana', '+77771234567', 'Looking for caregiver for my elderly mother', 'pass123'),
('amina.aminova@email.com', 'Amina', 'Aminova', 'Almaty', '+77771234568', 'Need babysitter for my 5-year-old son', 'pass123'),
('nurbol.nurbolov@email.com', 'Nurbol', 'Nurbolov', 'Astana', '+77771234569', 'Seeking playmate for my daughter', 'pass123'),
('ayzhan.ayzhanova@email.com', 'Ayzhan', 'Ayzhanova', 'Shymkent', '+77771234570', 'Elderly care needed for father', 'pass123'),
('daniyar.daniyarov@email.com', 'Daniyar', 'Daniyarov', 'Astana', '+77771234571', 'Babysitter for twins', 'pass123'),
('madina.madinova@email.com', 'Madina', 'Madinova', 'Almaty', '+77771234572', 'Playmate for active 7-year-old', 'pass123'),
('bekzhan.bekzhanov@email.com', 'Bekzhan', 'Bekzhanov', 'Astana', '+77771234573', 'Elderly care with medical needs', 'pass123'),
('aigerim.aigerimova@email.com', 'Aigerim', 'Aigerimova', 'Karaganda', '+77771234574', 'Babysitter for weekend events', 'pass123'),
('aslan.aslanov@email.com', 'Aslan', 'Aslanov', 'Astana', '+77771234575', 'Regular babysitting services needed', 'pass123'),
('zhuldyz.zhuldyzova@email.com', 'Zhuldyz', 'Zhuldyzova', 'Almaty', '+77771234576', 'Elderly care with house rules', 'pass123'),
('nazira.nazirova@email.com', 'Nazira', 'Nazirova', 'Astana', '+77771234577', 'Need elderly care for my mother', 'pass123');

-- Insert Caregivers (10 instances)
INSERT INTO caregiver (caregiver_user_id, photo, gender, caregiving_type, hourly_rate) VALUES
(1, 'photo1.jpg', 'Female', 'babysitter', 15.00),
(2, 'photo2.jpg', 'Male', 'elderly care', 20.00),
(3, 'photo3.jpg', 'Female', 'playmate', 12.00),
(4, 'photo4.jpg', 'Male', 'babysitter', 18.00),
(5, 'photo5.jpg', 'Female', 'elderly care', 22.00),
(6, 'photo6.jpg', 'Male', 'playmate', 14.00),
(7, 'photo7.jpg', 'Female', 'babysitter', 16.00),
(8, 'photo8.jpg', 'Male', 'elderly care', 25.00),
(9, 'photo9.jpg', 'Female', 'playmate', 13.00),
(10, 'photo10.jpg', 'Male', 'babysitter', 17.00);

-- Insert Members (10 instances)
INSERT INTO member (member_user_id, house_rules, dependent_description) VALUES
(11, 'No pets. Please maintain hygiene.', 'I have a 5-year-old son who likes painting and needs supervision'),
(12, 'No smoking. Soft-spoken caregiver preferred.', 'Elderly mother, 75 years old, needs assistance with daily activities'),
(13, 'Pets allowed. Creative activities welcome.', '7-year-old daughter who loves outdoor activities'),
(14, 'Strict hygiene rules. No pets.', 'Father, 80 years old, requires medical assistance'),
(15, 'No pets. Quiet environment needed.', 'Twin boys, 4 years old, need constant supervision'),
(16, 'Flexible rules. Soft-spoken preferred.', 'Active 7-year-old boy who loves sports'),
(17, 'Medical equipment present. No pets.', 'Elderly father with diabetes, needs medication management'),
(18, 'Weekend availability required. No pets.', '6-year-old daughter, needs occasional weekend care'),
(19, 'Regular schedule. No pets.', '8-year-old son, needs after-school care'),
(20, 'No pets. House rules must be followed strictly.', 'Elderly grandmother, 78 years old, needs companionship'),
(21, 'No pets. Clean environment required.', 'Elderly mother, 82 years old, needs daily assistance');

-- Insert Addresses (10 instances)
INSERT INTO address (member_user_id, house_number, street, town) VALUES
(11, '15', 'Kabanbay Batyr', 'Astana'),
(12, '23', 'Abay Avenue', 'Almaty'),
(13, '7', 'Nazarbayev Street', 'Astana'),
(14, '42', 'Turan Avenue', 'Shymkent'),
(15, '9', 'Kabanbay Batyr', 'Astana'),
(16, '31', 'Satpayev Street', 'Almaty'),
(17, '18', 'Kabanbay Batyr', 'Astana'),
(18, '55', 'Bukhar Zhyrau Avenue', 'Karaganda'),
(19, '12', 'Kabanbay Batyr', 'Astana'),
(20, '28', 'Raiymbek Avenue', 'Almaty'),
(21, '33', 'Nazarbayev Street', 'Astana');

-- Insert Jobs (10+ instances)
INSERT INTO job (member_user_id, required_caregiving_type, other_requirements, date_posted) VALUES
(11, 'babysitter', 'Must be soft-spoken and patient with children', '2025-01-15'),
(12, 'elderly care', 'Experience with medication management required', '2025-01-16'),
(13, 'playmate', 'Creative activities and outdoor games preferred', '2025-01-17'),
(14, 'elderly care', 'Medical background preferred, soft-spoken caregiver needed', '2025-01-18'),
(15, 'babysitter', 'Experience with multiple children required', '2025-01-19'),
(16, 'playmate', 'Sports activities and energetic personality', '2025-01-20'),
(17, 'elderly care', 'Diabetes management experience, soft-spoken preferred', '2025-01-21'),
(18, 'babysitter', 'Weekend availability essential', '2025-01-22'),
(19, 'babysitter', 'After-school hours, soft-spoken and reliable', '2025-01-23'),
(20, 'elderly care', 'Companionship and light housekeeping, soft-spoken caregiver', '2025-01-24'),
(11, 'playmate', 'Art and craft activities preferred', '2025-01-25'),
(12, 'elderly care', 'Physical therapy assistance needed', '2025-01-26'),
(21, 'elderly care', 'Daily care and medication assistance needed', '2025-01-27');

-- Insert Job Applications (10+ instances)
INSERT INTO job_application (caregiver_user_id, job_id, date_applied) VALUES
(1, 1, '2025-01-20'),
(2, 2, '2025-01-21'),
(3, 3, '2025-01-22'),
(4, 1, '2025-01-23'),
(5, 2, '2025-01-24'),
(6, 3, '2025-01-25'),
(7, 4, '2025-01-26'),
(8, 5, '2025-01-27'),
(9, 6, '2025-01-28'),
(10, 7, '2025-01-29'),
(1, 8, '2025-01-30'),
(2, 9, '2025-02-01'),
(3, 10, '2025-02-02'),
(4, 11, '2025-02-03'),
(5, 12, '2025-02-04');

-- Insert Appointments (10+ instances)
INSERT INTO appointment (caregiver_user_id, member_user_id, appointment_date, appointment_time, work_hours, status) VALUES
(1, 11, '2025-02-10', '09:00:00', 3.0, 'confirmed'),
(2, 12, '2025-02-11', '10:00:00', 4.0, 'confirmed'),
(3, 13, '2025-02-12', '14:00:00', 2.5, 'confirmed'),
(4, 15, '2025-02-13', '08:00:00', 5.0, 'confirmed'),
(5, 14, '2025-02-14', '09:00:00', 6.0, 'confirmed'),
(6, 16, '2025-02-15', '15:00:00', 3.5, 'confirmed'),
(7, 19, '2025-02-16', '16:00:00', 2.0, 'confirmed'),
(8, 17, '2025-02-17', '10:00:00', 4.5, 'confirmed'),
(9, 18, '2025-02-18', '11:00:00', 3.0, 'pending'),
(10, 20, '2025-02-19', '09:00:00', 5.0, 'declined'),
(1, 11, '2025-02-20', '13:00:00', 4.0, 'confirmed'),
(2, 12, '2025-02-21', '14:00:00', 3.5, 'confirmed'),
(3, 13, '2025-02-22', '10:00:00', 2.0, 'pending');

