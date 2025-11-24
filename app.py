"""
Part 3: Web Application with CRUD Operations
CSCI 341 - Assignment 3
Online Caregivers Platform

Flask web application providing CRUD operations for all database tables.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Database connection configuration
# Heroku provides DATABASE_URL automatically for PostgreSQL addons
# Heroku uses postgres:// but SQLAlchemy needs postgresql://
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Fix for Heroku: replace postgres:// with postgresql://
    if database_url.startswith('postgres://'):
        DATABASE_URL = database_url.replace('postgres://', 'postgresql://', 1)
    else:
        DATABASE_URL = database_url
else:
    # Local development configuration
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'caregivers_db')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pooling for Heroku
try:
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    
    # Auto-initialize database if tables don't exist
    def init_db():
        """Initialize database tables if they don't exist"""
        try:
            # Use begin() to ensure transaction
            with engine.begin() as conn:
                # Check if user table exists
                try:
                    result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'user'
                        );
                    """))
                    table_exists = result.fetchone()[0]
                except Exception as e:
                    # If we can't check, assume tables don't exist
                    print(f"Could not check if tables exist: {e}")
                    table_exists = False
                
                if not table_exists:
                    print("Database tables not found. Creating tables...")
                    
                    # Create tables - SQL embedded in code
                    create_tables_sql = """
                    -- Create USER table
                    CREATE TABLE IF NOT EXISTS "user" (
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
                    CREATE TABLE IF NOT EXISTS caregiver (
                        caregiver_user_id INTEGER PRIMARY KEY,
                        photo VARCHAR(500),
                        gender VARCHAR(20) NOT NULL,
                        caregiving_type VARCHAR(50) NOT NULL CHECK (caregiving_type IN ('babysitter', 'elderly care', 'playmate')),
                        hourly_rate DECIMAL(10, 2) NOT NULL CHECK (hourly_rate > 0),
                        FOREIGN KEY (caregiver_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
                    );
                    
                    -- Create MEMBER table
                    CREATE TABLE IF NOT EXISTS member (
                        member_user_id INTEGER PRIMARY KEY,
                        house_rules TEXT,
                        dependent_description TEXT,
                        FOREIGN KEY (member_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
                    );
                    
                    -- Create ADDRESS table
                    CREATE TABLE IF NOT EXISTS address (
                        member_user_id INTEGER PRIMARY KEY,
                        house_number VARCHAR(20) NOT NULL,
                        street VARCHAR(200) NOT NULL,
                        town VARCHAR(100) NOT NULL,
                        FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
                    );
                    
                    -- Create JOB table
                    CREATE TABLE IF NOT EXISTS job (
                        job_id SERIAL PRIMARY KEY,
                        member_user_id INTEGER NOT NULL,
                        required_caregiving_type VARCHAR(50) NOT NULL CHECK (required_caregiving_type IN ('babysitter', 'elderly care', 'playmate')),
                        other_requirements TEXT,
                        date_posted DATE NOT NULL DEFAULT CURRENT_DATE,
                        FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
                    );
                    
                    -- Create JOB_APPLICATION table
                    CREATE TABLE IF NOT EXISTS job_application (
                        caregiver_user_id INTEGER NOT NULL,
                        job_id INTEGER NOT NULL,
                        date_applied DATE NOT NULL DEFAULT CURRENT_DATE,
                        PRIMARY KEY (caregiver_user_id, job_id),
                        FOREIGN KEY (caregiver_user_id) REFERENCES caregiver(caregiver_user_id) ON DELETE CASCADE,
                        FOREIGN KEY (job_id) REFERENCES job(job_id) ON DELETE CASCADE
                    );
                    
                    -- Create APPOINTMENT table
                    CREATE TABLE IF NOT EXISTS appointment (
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
                    
                    -- Create indexes
                    CREATE INDEX IF NOT EXISTS idx_caregiver_type ON caregiver(caregiving_type);
                    CREATE INDEX IF NOT EXISTS idx_job_type ON job(required_caregiving_type);
                    CREATE INDEX IF NOT EXISTS idx_appointment_status ON appointment(status);
                    CREATE INDEX IF NOT EXISTS idx_appointment_date ON appointment(appointment_date);
                    CREATE INDEX IF NOT EXISTS idx_user_city ON "user"(city);
                    """
                    
                    # Execute table creation statements one by one
                    statements = [s.strip() for s in create_tables_sql.split(';') if s.strip() and not s.strip().startswith('--')]
                    
                    for statement in statements:
                        if statement:
                            try:
                                conn.execute(text(statement))
                            except Exception as e:
                                error_msg = str(e).lower()
                                if "already exists" not in error_msg and "duplicate" not in error_msg:
                                    print(f"Error creating table: {str(e)[:200]}")
                                    print(f"Statement was: {statement[:150]}")
                                    # Don't stop on errors, continue creating other tables
                    
                    # Verify all tables were created
                    required_tables = ['user', 'caregiver', 'member', 'address', 'job', 'job_application', 'appointment']
                    missing_tables = []
                    for table_name in required_tables:
                        check_query = text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_schema = 'public' 
                                AND table_name = '{table_name}'
                            );
                        """)
                        result = conn.execute(check_query)
                        if not result.fetchone()[0]:
                            missing_tables.append(table_name)
                    
                    if missing_tables:
                        print(f"ERROR: Some tables were not created: {missing_tables}")
                        print("Attempting to create missing tables individually...")
                        # Try to create missing tables individually
                        for table_name in missing_tables:
                            if table_name == 'caregiver':
                                try:
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS caregiver (
                                            caregiver_user_id INTEGER PRIMARY KEY,
                                            photo VARCHAR(500),
                                            gender VARCHAR(20) NOT NULL,
                                            caregiving_type VARCHAR(50) NOT NULL CHECK (caregiving_type IN ('babysitter', 'elderly care', 'playmate')),
                                            hourly_rate DECIMAL(10, 2) NOT NULL CHECK (hourly_rate > 0),
                                            FOREIGN KEY (caregiver_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
                                        );
                                    """))
                                    conn.commit()
                                    print(f"Created table: {table_name}")
                                except Exception as e:
                                    print(f"Failed to create {table_name}: {e}")
                            elif table_name == 'member':
                                try:
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS member (
                                            member_user_id INTEGER PRIMARY KEY,
                                            house_rules TEXT,
                                            dependent_description TEXT,
                                            FOREIGN KEY (member_user_id) REFERENCES "user"(user_id) ON DELETE CASCADE
                                        );
                                    """))
                                    conn.commit()
                                    print(f"Created table: {table_name}")
                                except Exception as e:
                                    print(f"Failed to create {table_name}: {e}")
                            elif table_name == 'address':
                                try:
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS address (
                                            member_user_id INTEGER PRIMARY KEY,
                                            house_number VARCHAR(20) NOT NULL,
                                            street VARCHAR(200) NOT NULL,
                                            town VARCHAR(100) NOT NULL,
                                            FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
                                        );
                                    """))
                                    conn.commit()
                                    print(f"Created table: {table_name}")
                                except Exception as e:
                                    print(f"Failed to create {table_name}: {e}")
                            elif table_name == 'job':
                                try:
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS job (
                                            job_id SERIAL PRIMARY KEY,
                                            member_user_id INTEGER NOT NULL,
                                            required_caregiving_type VARCHAR(50) NOT NULL CHECK (required_caregiving_type IN ('babysitter', 'elderly care', 'playmate')),
                                            other_requirements TEXT,
                                            date_posted DATE NOT NULL DEFAULT CURRENT_DATE,
                                            FOREIGN KEY (member_user_id) REFERENCES member(member_user_id) ON DELETE CASCADE
                                        );
                                    """))
                                    conn.commit()
                                    print(f"Created table: {table_name}")
                                except Exception as e:
                                    print(f"Failed to create {table_name}: {e}")
                            elif table_name == 'job_application':
                                try:
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS job_application (
                                            caregiver_user_id INTEGER NOT NULL,
                                            job_id INTEGER NOT NULL,
                                            date_applied DATE NOT NULL DEFAULT CURRENT_DATE,
                                            PRIMARY KEY (caregiver_user_id, job_id),
                                            FOREIGN KEY (caregiver_user_id) REFERENCES caregiver(caregiver_user_id) ON DELETE CASCADE,
                                            FOREIGN KEY (job_id) REFERENCES job(job_id) ON DELETE CASCADE
                                        );
                                    """))
                                    conn.commit()
                                    print(f"Created table: {table_name}")
                                except Exception as e:
                                    print(f"Failed to create {table_name}: {e}")
                            elif table_name == 'appointment':
                                try:
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS appointment (
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
                                    """))
                                    conn.commit()
                                    print(f"Created table: {table_name}")
                                except Exception as e:
                                    print(f"Failed to create {table_name}: {e}")
                    else:
                        print("Database tables created successfully!")
                    
                    # Insert sample data if tables are empty
                    try:
                        # Check if data already exists
                        result = conn.execute(text("SELECT COUNT(*) FROM \"user\""))
                        user_count = result.fetchone()[0]
                        
                        if user_count == 0:
                            print("Inserting sample data...")
                            
                            # Insert Users
                            insert_users = """
                            INSERT INTO "user" (email, given_name, surname, city, phone_number, profile_description, password) VALUES
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
                            """
                            
                            conn.execute(text(insert_users))
                            conn.commit()
                            
                            # Insert Caregivers
                            insert_caregivers = """
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
                            """
                            
                            conn.execute(text(insert_caregivers))
                            conn.commit()
                            
                            # Insert Members
                            insert_members = """
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
                            """
                            
                            conn.execute(text(insert_members))
                            conn.commit()
                            
                            # Insert Addresses
                            insert_addresses = """
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
                            """
                            
                            conn.execute(text(insert_addresses))
                            conn.commit()
                            
                            # Insert Jobs
                            insert_jobs = """
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
                            """
                            
                            conn.execute(text(insert_jobs))
                            conn.commit()
                            
                            # Insert Job Applications
                            insert_applications = """
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
                            """
                            
                            conn.execute(text(insert_applications))
                            conn.commit()
                            
                            # Insert Appointments
                            insert_appointments = """
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
                            """
                            
                            conn.execute(text(insert_appointments))
                            conn.commit()
                            
                            print("Sample data inserted successfully!")
                        else:
                            print(f"Database already contains {user_count} users. Skipping data insertion.")
                    except Exception as e:
                        print(f"Warning inserting data: {str(e)[:200]}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            print(f"Error initializing database: {e}")
            import traceback
            traceback.print_exc()
    
    # Initialize on startup (always, but only create tables if they don't exist)
    # This ensures tables are created on Heroku
    print("Starting database initialization...")
    try:
        init_db()
        print("Database initialization completed.")
    except Exception as e:
        print(f"ERROR: Could not initialize database on startup: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the app startup, but log the error
        # Try to initialize again on first request
        print("Will retry initialization on first database access...")
    
except Exception as e:
    print(f"Database connection error: {e}")
    print(f"DATABASE_URL present: {bool(os.getenv('DATABASE_URL'))}")
    raise


def get_session():
    """Get a new database session"""
    # Check if tables exist before returning session
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user'
                );
            """))
            if not result.fetchone()[0]:
                print("Tables not found during session creation. Initializing...")
                init_db()
    except Exception as e:
        print(f"Warning checking tables: {e}")
        # Try to initialize anyway
        try:
            init_db()
        except:
            pass
    return Session()


# ============================================================================
# HOME PAGE
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


# ============================================================================
# USER CRUD OPERATIONS
# ============================================================================

@app.route('/users')
def list_users():
    """List all users"""
    session = get_session()
    try:
        query = text("SELECT * FROM \"user\" ORDER BY user_id")
        result = session.execute(query)
        users = [dict(row._mapping) for row in result]
        return render_template('users/list.html', users=users)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('users/list.html', users=[])
    finally:
        session.close()


@app.route('/users/create', methods=['GET', 'POST'])
def create_user():
    """Create a new user"""
    if request.method == 'POST':
        session = get_session()
        try:
            query = text("""
                INSERT INTO "user" (email, given_name, surname, city, phone_number, profile_description, password)
                VALUES (:email, :given_name, :surname, :city, :phone_number, :profile_description, :password)
            """)
            session.execute(query, {
                'email': request.form['email'],
                'given_name': request.form['given_name'],
                'surname': request.form['surname'],
                'city': request.form['city'],
                'phone_number': request.form['phone_number'],
                'profile_description': request.form.get('profile_description', ''),
                'password': request.form['password']
            })
            session.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating user: {e}', 'error')
        finally:
            session.close()
    return render_template('users/create.html')


@app.route('/users/<int:user_id>/update', methods=['GET', 'POST'])
def update_user(user_id):
    """Update a user"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                UPDATE "user"
                SET email = :email, given_name = :given_name, surname = :surname,
                    city = :city, phone_number = :phone_number,
                    profile_description = :profile_description, password = :password
                WHERE user_id = :user_id
            """)
            session.execute(query, {
                'user_id': user_id,
                'email': request.form['email'],
                'given_name': request.form['given_name'],
                'surname': request.form['surname'],
                'city': request.form['city'],
                'phone_number': request.form['phone_number'],
                'profile_description': request.form.get('profile_description', ''),
                'password': request.form['password']
            })
            session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('list_users'))
        except Exception as e:
            session.rollback()
            flash(f'Error updating user: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch user data
    try:
        query = text("SELECT * FROM \"user\" WHERE user_id = :user_id")
        result = session.execute(query, {'user_id': user_id})
        user = dict(result.fetchone()._mapping)
        return render_template('users/update.html', user=user)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_users'))
    finally:
        session.close()


@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    session = get_session()
    try:
        query = text("DELETE FROM \"user\" WHERE user_id = :user_id")
        session.execute(query, {'user_id': user_id})
        session.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting user: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_users'))


# ============================================================================
# CAREGIVER CRUD OPERATIONS
# ============================================================================

@app.route('/caregivers')
def list_caregivers():
    """List all caregivers"""
    session = get_session()
    try:
        query = text("""
            SELECT c.*, u.given_name, u.surname, u.email, u.city, u.phone_number
            FROM caregiver c
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            ORDER BY c.caregiver_user_id
        """)
        result = session.execute(query)
        caregivers = [dict(row._mapping) for row in result]
        return render_template('caregivers/list.html', caregivers=caregivers)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('caregivers/list.html', caregivers=[])
    finally:
        session.close()


@app.route('/caregivers/create', methods=['GET', 'POST'])
def create_caregiver():
    """Create a new caregiver"""
    session = get_session()
    if request.method == 'POST':
        try:
            # First create user, then caregiver
            user_query = text("""
                INSERT INTO "user" (email, given_name, surname, city, phone_number, profile_description, password)
                VALUES (:email, :given_name, :surname, :city, :phone_number, :profile_description, :password)
                RETURNING user_id
            """)
            result = session.execute(user_query, {
                'email': request.form['email'],
                'given_name': request.form['given_name'],
                'surname': request.form['surname'],
                'city': request.form['city'],
                'phone_number': request.form['phone_number'],
                'profile_description': request.form.get('profile_description', ''),
                'password': request.form['password']
            })
            user_id = result.fetchone()[0]
            
            caregiver_query = text("""
                INSERT INTO caregiver (caregiver_user_id, photo, gender, caregiving_type, hourly_rate)
                VALUES (:user_id, :photo, :gender, :caregiving_type, :hourly_rate)
            """)
            session.execute(caregiver_query, {
                'user_id': user_id,
                'photo': request.form.get('photo', ''),
                'gender': request.form['gender'],
                'caregiving_type': request.form['caregiving_type'],
                'hourly_rate': float(request.form['hourly_rate'])
            })
            session.commit()
            flash('Caregiver created successfully!', 'success')
            return redirect(url_for('list_caregivers'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating caregiver: {e}', 'error')
        finally:
            session.close()
    
    # GET: Show form
    return render_template('caregivers/create.html')


@app.route('/caregivers/<int:caregiver_id>/update', methods=['GET', 'POST'])
def update_caregiver(caregiver_id):
    """Update a caregiver"""
    session = get_session()
    if request.method == 'POST':
        try:
            # Update user info
            user_query = text("""
                UPDATE "user"
                SET email = :email, given_name = :given_name, surname = :surname,
                    city = :city, phone_number = :phone_number,
                    profile_description = :profile_description, password = :password
                WHERE user_id = :user_id
            """)
            session.execute(user_query, {
                'user_id': caregiver_id,
                'email': request.form['email'],
                'given_name': request.form['given_name'],
                'surname': request.form['surname'],
                'city': request.form['city'],
                'phone_number': request.form['phone_number'],
                'profile_description': request.form.get('profile_description', ''),
                'password': request.form['password']
            })
            
            # Update caregiver info
            caregiver_query = text("""
                UPDATE caregiver
                SET photo = :photo, gender = :gender, caregiving_type = :caregiving_type,
                    hourly_rate = :hourly_rate
                WHERE caregiver_user_id = :user_id
            """)
            session.execute(caregiver_query, {
                'user_id': caregiver_id,
                'photo': request.form.get('photo', ''),
                'gender': request.form['gender'],
                'caregiving_type': request.form['caregiving_type'],
                'hourly_rate': float(request.form['hourly_rate'])
            })
            session.commit()
            flash('Caregiver updated successfully!', 'success')
            return redirect(url_for('list_caregivers'))
        except Exception as e:
            session.rollback()
            flash(f'Error updating caregiver: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch caregiver data
    try:
        query = text("""
            SELECT c.*, u.email, u.given_name, u.surname, u.city, u.phone_number, u.profile_description, u.password
            FROM caregiver c
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            WHERE c.caregiver_user_id = :caregiver_id
        """)
        result = session.execute(query, {'caregiver_id': caregiver_id})
        caregiver = dict(result.fetchone()._mapping)
        return render_template('caregivers/update.html', caregiver=caregiver)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_caregivers'))
    finally:
        session.close()


@app.route('/caregivers/<int:caregiver_id>/delete', methods=['POST'])
def delete_caregiver(caregiver_id):
    """Delete a caregiver"""
    session = get_session()
    try:
        query = text("DELETE FROM \"user\" WHERE user_id = :user_id")
        session.execute(query, {'user_id': caregiver_id})
        session.commit()
        flash('Caregiver deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting caregiver: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_caregivers'))


# ============================================================================
# MEMBER CRUD OPERATIONS
# ============================================================================

@app.route('/members')
def list_members():
    """List all members"""
    session = get_session()
    try:
        query = text("""
            SELECT m.*, u.given_name, u.surname, u.email, u.city, u.phone_number
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY m.member_user_id
        """)
        result = session.execute(query)
        members = [dict(row._mapping) for row in result]
        return render_template('members/list.html', members=members)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('members/list.html', members=[])
    finally:
        session.close()


@app.route('/members/create', methods=['GET', 'POST'])
def create_member():
    """Create a new member"""
    session = get_session()
    if request.method == 'POST':
        try:
            # First create user, then member
            user_query = text("""
                INSERT INTO "user" (email, given_name, surname, city, phone_number, profile_description, password)
                VALUES (:email, :given_name, :surname, :city, :phone_number, :profile_description, :password)
                RETURNING user_id
            """)
            result = session.execute(user_query, {
                'email': request.form['email'],
                'given_name': request.form['given_name'],
                'surname': request.form['surname'],
                'city': request.form['city'],
                'phone_number': request.form['phone_number'],
                'profile_description': request.form.get('profile_description', ''),
                'password': request.form['password']
            })
            user_id = result.fetchone()[0]
            
            member_query = text("""
                INSERT INTO member (member_user_id, house_rules, dependent_description)
                VALUES (:user_id, :house_rules, :dependent_description)
            """)
            session.execute(member_query, {
                'user_id': user_id,
                'house_rules': request.form.get('house_rules', ''),
                'dependent_description': request.form.get('dependent_description', '')
            })
            session.commit()
            flash('Member created successfully!', 'success')
            return redirect(url_for('list_members'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating member: {e}', 'error')
        finally:
            session.close()
    
    return render_template('members/create.html')


@app.route('/members/<int:member_id>/update', methods=['GET', 'POST'])
def update_member(member_id):
    """Update a member"""
    session = get_session()
    if request.method == 'POST':
        try:
            # Update user info
            user_query = text("""
                UPDATE "user"
                SET email = :email, given_name = :given_name, surname = :surname,
                    city = :city, phone_number = :phone_number,
                    profile_description = :profile_description, password = :password
                WHERE user_id = :user_id
            """)
            session.execute(user_query, {
                'user_id': member_id,
                'email': request.form['email'],
                'given_name': request.form['given_name'],
                'surname': request.form['surname'],
                'city': request.form['city'],
                'phone_number': request.form['phone_number'],
                'profile_description': request.form.get('profile_description', ''),
                'password': request.form['password']
            })
            
            # Update member info
            member_query = text("""
                UPDATE member
                SET house_rules = :house_rules, dependent_description = :dependent_description
                WHERE member_user_id = :user_id
            """)
            session.execute(member_query, {
                'user_id': member_id,
                'house_rules': request.form.get('house_rules', ''),
                'dependent_description': request.form.get('dependent_description', '')
            })
            session.commit()
            flash('Member updated successfully!', 'success')
            return redirect(url_for('list_members'))
        except Exception as e:
            session.rollback()
            flash(f'Error updating member: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch member data
    try:
        query = text("""
            SELECT m.*, u.email, u.given_name, u.surname, u.city, u.phone_number, u.profile_description, u.password
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            WHERE m.member_user_id = :member_id
        """)
        result = session.execute(query, {'member_id': member_id})
        member = dict(result.fetchone()._mapping)
        return render_template('members/update.html', member=member)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_members'))
    finally:
        session.close()


@app.route('/members/<int:member_id>/delete', methods=['POST'])
def delete_member(member_id):
    """Delete a member"""
    session = get_session()
    try:
        query = text("DELETE FROM \"user\" WHERE user_id = :user_id")
        session.execute(query, {'user_id': member_id})
        session.commit()
        flash('Member deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting member: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_members'))


# ============================================================================
# ADDRESS CRUD OPERATIONS
# ============================================================================

@app.route('/addresses')
def list_addresses():
    """List all addresses"""
    session = get_session()
    try:
        query = text("""
            SELECT a.*, u.given_name, u.surname
            FROM address a
            JOIN member m ON a.member_user_id = m.member_user_id
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY a.member_user_id
        """)
        result = session.execute(query)
        addresses = [dict(row._mapping) for row in result]
        return render_template('addresses/list.html', addresses=addresses)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('addresses/list.html', addresses=[])
    finally:
        session.close()


@app.route('/addresses/create', methods=['GET', 'POST'])
def create_address():
    """Create a new address"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                INSERT INTO address (member_user_id, house_number, street, town)
                VALUES (:member_user_id, :house_number, :street, :town)
            """)
            session.execute(query, {
                'member_user_id': int(request.form['member_user_id']),
                'house_number': request.form['house_number'],
                'street': request.form['street'],
                'town': request.form['town']
            })
            session.commit()
            flash('Address created successfully!', 'success')
            return redirect(url_for('list_addresses'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating address: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch members for dropdown
    try:
        query = text("""
            SELECT m.member_user_id, u.given_name || ' ' || u.surname AS name
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY u.surname
        """)
        result = session.execute(query)
        members = [dict(row._mapping) for row in result]
        return render_template('addresses/create.html', members=members)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_addresses'))
    finally:
        session.close()


@app.route('/addresses/<int:member_id>/update', methods=['GET', 'POST'])
def update_address(member_id):
    """Update an address"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                UPDATE address
                SET house_number = :house_number, street = :street, town = :town
                WHERE member_user_id = :member_user_id
            """)
            session.execute(query, {
                'member_user_id': member_id,
                'house_number': request.form['house_number'],
                'street': request.form['street'],
                'town': request.form['town']
            })
            session.commit()
            flash('Address updated successfully!', 'success')
            return redirect(url_for('list_addresses'))
        except Exception as e:
            session.rollback()
            flash(f'Error updating address: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch address data
    try:
        query = text("SELECT * FROM address WHERE member_user_id = :member_id")
        result = session.execute(query, {'member_id': member_id})
        address = dict(result.fetchone()._mapping)
        return render_template('addresses/update.html', address=address)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_addresses'))
    finally:
        session.close()


@app.route('/addresses/<int:member_id>/delete', methods=['POST'])
def delete_address(member_id):
    """Delete an address"""
    session = get_session()
    try:
        query = text("DELETE FROM address WHERE member_user_id = :member_id")
        session.execute(query, {'member_id': member_id})
        session.commit()
        flash('Address deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting address: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_addresses'))


# ============================================================================
# JOB CRUD OPERATIONS
# ============================================================================

@app.route('/jobs')
def list_jobs():
    """List all jobs"""
    session = get_session()
    try:
        query = text("""
            SELECT j.*, u.given_name || ' ' || u.surname AS member_name
            FROM job j
            JOIN member m ON j.member_user_id = m.member_user_id
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY j.job_id
        """)
        result = session.execute(query)
        jobs = [dict(row._mapping) for row in result]
        return render_template('jobs/list.html', jobs=jobs)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('jobs/list.html', jobs=[])
    finally:
        session.close()


@app.route('/jobs/create', methods=['GET', 'POST'])
def create_job():
    """Create a new job"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                INSERT INTO job (member_user_id, required_caregiving_type, other_requirements, date_posted)
                VALUES (:member_user_id, :required_caregiving_type, :other_requirements, :date_posted)
            """)
            session.execute(query, {
                'member_user_id': int(request.form['member_user_id']),
                'required_caregiving_type': request.form['required_caregiving_type'],
                'other_requirements': request.form.get('other_requirements', ''),
                'date_posted': request.form.get('date_posted', date.today())
            })
            session.commit()
            flash('Job created successfully!', 'success')
            return redirect(url_for('list_jobs'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating job: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch members for dropdown
    try:
        query = text("""
            SELECT m.member_user_id, u.given_name || ' ' || u.surname AS name
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY u.surname
        """)
        result = session.execute(query)
        members = [dict(row._mapping) for row in result]
        return render_template('jobs/create.html', members=members)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_jobs'))
    finally:
        session.close()


@app.route('/jobs/<int:job_id>/update', methods=['GET', 'POST'])
def update_job(job_id):
    """Update a job"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                UPDATE job
                SET member_user_id = :member_user_id, required_caregiving_type = :required_caregiving_type,
                    other_requirements = :other_requirements, date_posted = :date_posted
                WHERE job_id = :job_id
            """)
            session.execute(query, {
                'job_id': job_id,
                'member_user_id': int(request.form['member_user_id']),
                'required_caregiving_type': request.form['required_caregiving_type'],
                'other_requirements': request.form.get('other_requirements', ''),
                'date_posted': request.form.get('date_posted')
            })
            session.commit()
            flash('Job updated successfully!', 'success')
            return redirect(url_for('list_jobs'))
        except Exception as e:
            session.rollback()
            flash(f'Error updating job: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch job data
    try:
        query = text("SELECT * FROM job WHERE job_id = :job_id")
        result = session.execute(query, {'job_id': job_id})
        job = dict(result.fetchone()._mapping)
        
        # Get members for dropdown
        members_query = text("""
            SELECT m.member_user_id, u.given_name || ' ' || u.surname AS name
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY u.surname
        """)
        members_result = session.execute(members_query)
        members = [dict(row._mapping) for row in members_result]
        
        return render_template('jobs/update.html', job=job, members=members)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_jobs'))
    finally:
        session.close()


@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job"""
    session = get_session()
    try:
        query = text("DELETE FROM job WHERE job_id = :job_id")
        session.execute(query, {'job_id': job_id})
        session.commit()
        flash('Job deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting job: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_jobs'))


# ============================================================================
# JOB APPLICATION CRUD OPERATIONS
# ============================================================================

@app.route('/job_applications')
def list_job_applications():
    """List all job applications"""
    session = get_session()
    try:
        query = text("""
            SELECT ja.*, 
                   u_cg.given_name || ' ' || u_cg.surname AS caregiver_name,
                   u_m.given_name || ' ' || u_m.surname AS member_name,
                   j.required_caregiving_type
            FROM job_application ja
            JOIN caregiver c ON ja.caregiver_user_id = c.caregiver_user_id
            JOIN "user" u_cg ON c.caregiver_user_id = u_cg.user_id
            JOIN job j ON ja.job_id = j.job_id
            JOIN member m ON j.member_user_id = m.member_user_id
            JOIN "user" u_m ON m.member_user_id = u_m.user_id
            ORDER BY ja.job_id, ja.date_applied
        """)
        result = session.execute(query)
        applications = [dict(row._mapping) for row in result]
        return render_template('job_applications/list.html', applications=applications)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('job_applications/list.html', applications=[])
    finally:
        session.close()


@app.route('/job_applications/create', methods=['GET', 'POST'])
def create_job_application():
    """Create a new job application"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                INSERT INTO job_application (caregiver_user_id, job_id, date_applied)
                VALUES (:caregiver_user_id, :job_id, :date_applied)
            """)
            session.execute(query, {
                'caregiver_user_id': int(request.form['caregiver_user_id']),
                'job_id': int(request.form['job_id']),
                'date_applied': request.form.get('date_applied', date.today())
            })
            session.commit()
            flash('Job application created successfully!', 'success')
            return redirect(url_for('list_job_applications'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating job application: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch caregivers and jobs for dropdowns
    try:
        caregivers_query = text("""
            SELECT c.caregiver_user_id, u.given_name || ' ' || u.surname AS name
            FROM caregiver c
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            ORDER BY u.surname
        """)
        jobs_query = text("""
            SELECT j.job_id, j.required_caregiving_type, u.given_name || ' ' || u.surname AS member_name
            FROM job j
            JOIN member m ON j.member_user_id = m.member_user_id
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY j.job_id
        """)
        caregivers = [dict(row._mapping) for row in session.execute(caregivers_query)]
        jobs = [dict(row._mapping) for row in session.execute(jobs_query)]
        return render_template('job_applications/create.html', caregivers=caregivers, jobs=jobs)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_job_applications'))
    finally:
        session.close()


@app.route('/job_applications/<int:caregiver_id>/<int:job_id>/delete', methods=['POST'])
def delete_job_application(caregiver_id, job_id):
    """Delete a job application"""
    session = get_session()
    try:
        query = text("""
            DELETE FROM job_application
            WHERE caregiver_user_id = :caregiver_id AND job_id = :job_id
        """)
        session.execute(query, {'caregiver_id': caregiver_id, 'job_id': job_id})
        session.commit()
        flash('Job application deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting job application: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_job_applications'))


# ============================================================================
# APPOINTMENT CRUD OPERATIONS
# ============================================================================

@app.route('/appointments')
def list_appointments():
    """List all appointments"""
    session = get_session()
    try:
        query = text("""
            SELECT a.*,
                   u_cg.given_name || ' ' || u_cg.surname AS caregiver_name,
                   u_m.given_name || ' ' || u_m.surname AS member_name
            FROM appointment a
            JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
            JOIN "user" u_cg ON c.caregiver_user_id = u_cg.user_id
            JOIN member m ON a.member_user_id = m.member_user_id
            JOIN "user" u_m ON m.member_user_id = u_m.user_id
            ORDER BY a.appointment_date DESC, a.appointment_time
        """)
        result = session.execute(query)
        appointments = [dict(row._mapping) for row in result]
        return render_template('appointments/list.html', appointments=appointments)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return render_template('appointments/list.html', appointments=[])
    finally:
        session.close()


@app.route('/appointments/create', methods=['GET', 'POST'])
def create_appointment():
    """Create a new appointment"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                INSERT INTO appointment (caregiver_user_id, member_user_id, appointment_date, appointment_time, work_hours, status)
                VALUES (:caregiver_user_id, :member_user_id, :appointment_date, :appointment_time, :work_hours, :status)
            """)
            session.execute(query, {
                'caregiver_user_id': int(request.form['caregiver_user_id']),
                'member_user_id': int(request.form['member_user_id']),
                'appointment_date': request.form['appointment_date'],
                'appointment_time': request.form['appointment_time'],
                'work_hours': float(request.form['work_hours']),
                'status': request.form.get('status', 'pending')
            })
            session.commit()
            flash('Appointment created successfully!', 'success')
            return redirect(url_for('list_appointments'))
        except Exception as e:
            session.rollback()
            flash(f'Error creating appointment: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch caregivers and members for dropdowns
    try:
        caregivers_query = text("""
            SELECT c.caregiver_user_id, u.given_name || ' ' || u.surname AS name
            FROM caregiver c
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            ORDER BY u.surname
        """)
        members_query = text("""
            SELECT m.member_user_id, u.given_name || ' ' || u.surname AS name
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY u.surname
        """)
        caregivers = [dict(row._mapping) for row in session.execute(caregivers_query)]
        members = [dict(row._mapping) for row in session.execute(members_query)]
        return render_template('appointments/create.html', caregivers=caregivers, members=members)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_appointments'))
    finally:
        session.close()


@app.route('/appointments/<int:appointment_id>/update', methods=['GET', 'POST'])
def update_appointment(appointment_id):
    """Update an appointment"""
    session = get_session()
    if request.method == 'POST':
        try:
            query = text("""
                UPDATE appointment
                SET caregiver_user_id = :caregiver_user_id, member_user_id = :member_user_id,
                    appointment_date = :appointment_date, appointment_time = :appointment_time,
                    work_hours = :work_hours, status = :status
                WHERE appointment_id = :appointment_id
            """)
            session.execute(query, {
                'appointment_id': appointment_id,
                'caregiver_user_id': int(request.form['caregiver_user_id']),
                'member_user_id': int(request.form['member_user_id']),
                'appointment_date': request.form['appointment_date'],
                'appointment_time': request.form['appointment_time'],
                'work_hours': float(request.form['work_hours']),
                'status': request.form['status']
            })
            session.commit()
            flash('Appointment updated successfully!', 'success')
            return redirect(url_for('list_appointments'))
        except Exception as e:
            session.rollback()
            flash(f'Error updating appointment: {e}', 'error')
        finally:
            session.close()
    
    # GET: Fetch appointment data
    try:
        query = text("SELECT * FROM appointment WHERE appointment_id = :appointment_id")
        result = session.execute(query, {'appointment_id': appointment_id})
        appointment = dict(result.fetchone()._mapping)
        
        # Get caregivers and members for dropdowns
        caregivers_query = text("""
            SELECT c.caregiver_user_id, u.given_name || ' ' || u.surname AS name
            FROM caregiver c
            JOIN "user" u ON c.caregiver_user_id = u.user_id
            ORDER BY u.surname
        """)
        members_query = text("""
            SELECT m.member_user_id, u.given_name || ' ' || u.surname AS name
            FROM member m
            JOIN "user" u ON m.member_user_id = u.user_id
            ORDER BY u.surname
        """)
        caregivers = [dict(row._mapping) for row in session.execute(caregivers_query)]
        members = [dict(row._mapping) for row in session.execute(members_query)]
        
        return render_template('appointments/update.html', appointment=appointment, caregivers=caregivers, members=members)
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('list_appointments'))
    finally:
        session.close()


@app.route('/appointments/<int:appointment_id>/delete', methods=['POST'])
def delete_appointment(appointment_id):
    """Delete an appointment"""
    session = get_session()
    try:
        query = text("DELETE FROM appointment WHERE appointment_id = :appointment_id")
        session.execute(query, {'appointment_id': appointment_id})
        session.commit()
        flash('Appointment deleted successfully!', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error deleting appointment: {e}', 'error')
    finally:
        session.close()
    return redirect(url_for('list_appointments'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

