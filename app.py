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

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def get_session():
    """Get a new database session"""
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

