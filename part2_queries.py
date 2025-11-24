from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os


DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'caregivers_db')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()


def print_separator(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def execute_and_display(query, description):
    print_separator(description)
    try:
        result = session.execute(text(query))
        rows = result.fetchall()
        
        if rows:
            columns = result.keys()
            print(f"Columns: {', '.join(columns)}")
            print(f"Number of rows: {len(rows)}\n")
            
            for row in rows:
                print(row)
        else:
            print("No results found.")
    except Exception as e:
        print(f"Error: {e}")
    print()


def main():
    print("="*80)
    print("  CSCI 341 Assignment 3 - Part 2")
    print("  Online Caregivers Platform Queries")
    print("="*80)
    
    # CREATE statements
    print_separator("1. CREATE SQL STATEMENTS")
    print("Tables should be created using schema.sql file first.")
    print("Run: psql -U postgres -d caregivers_db -f schema.sql")
    
    # INSERT statements
    print_separator("2. INSERT SQL STATEMENTS")
    print("Data should be inserted using insert_data.sql file.")
    print("Run: psql -U postgres -d caregivers_db -f insert_data.sql")
    
    # UPDATE statements
    print_separator("3. UPDATE SQL STATEMENTS")
    
    # 3.1 Update Arman Armanov's phone number
    print("3.1 Updating Arman Armanov phone number to +77773414141")
    update1 = """
    UPDATE "user"
    SET phone_number = '+77773414141'
    WHERE given_name = 'Arman' AND surname = 'Armanov';
    """
    try:
        session.execute(text(update1))
        session.commit()
        print("Success! Phone number updated")
        
        # Check if it worked
        check = """
        SELECT user_id, given_name, surname, phone_number
        FROM "user"
        WHERE given_name = 'Arman' AND surname = 'Armanov';
        """
        result = session.execute(text(check))
        row = result.fetchone()
        print(f"Updated record: {row}")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    
    # 3.2 Update hourly rates with commission
    print("\n3.2 Adding commission to caregiver hourly rates")
    update2 = """
    UPDATE caregiver
    SET hourly_rate = CASE
        WHEN hourly_rate < 10 THEN hourly_rate + 0.3
        ELSE hourly_rate * 1.10
    END;
    """
    try:
        session.execute(text(update2))
        session.commit()
        print("Success! Hourly rates updated")
        
        # Show updated rates
        check = """
        SELECT caregiver_user_id, hourly_rate
        FROM caregiver
        ORDER BY caregiver_user_id;
        """
        result = session.execute(text(check))
        print("\nUpdated rates:")
        for row in result:
            print(f"  Caregiver {row[0]}: ${row[1]:.2f}")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    
    # DELETE statements
    print_separator("4. DELETE SQL STATEMENTS")
    
    # 4.1 Delete Amina Aminova's jobs
    print("4.1 Deleting jobs posted by Amina Aminova")
    delete1 = """
    DELETE FROM job
    WHERE member_user_id IN (
        SELECT user_id
        FROM "user"
        WHERE given_name = 'Amina' AND surname = 'Aminova'
    );
    """
    try:
        result = session.execute(text(delete1))
        session.commit()
        print(f"Deleted {result.rowcount} job(s)")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    
    # 4.2 Delete members on Kabanbay Batyr street
    print("\n4.2 Deleting members who live on Kabanbay Batyr street")
    delete2 = """
    DELETE FROM member
    WHERE member_user_id IN (
        SELECT member_user_id
        FROM address
        WHERE street = 'Kabanbay Batyr'
    );
    """
    try:
        result = session.execute(text(delete2))
        session.commit()
        print(f"Deleted {result.rowcount} member(s)")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    
    # Simple queries
    print_separator("5. SIMPLE QUERIES")
    
    # 5.1 Names for confirmed appointments
    query1 = """
    SELECT 
        cg.given_name || ' ' || cg.surname AS caregiver_name,
        m.given_name || ' ' || m.surname AS member_name
    FROM appointment a
    JOIN "user" cg ON a.caregiver_user_id = cg.user_id
    JOIN "user" m ON a.member_user_id = m.user_id
    WHERE a.status = 'confirmed';
    """
    execute_and_display(query1, "5.1 Caregiver and Member Names for Confirmed Appointments")
    
    # 5.2 Jobs with 'soft-spoken' in requirements
    query2 = """
    SELECT job_id, other_requirements
    FROM job
    WHERE other_requirements LIKE '%soft-spoken%';
    """
    execute_and_display(query2, "5.2 Jobs with 'soft-spoken' in Requirements")
    
    # 5.3 Work hours for babysitters
    query3 = """
    SELECT a.appointment_id, a.work_hours, a.appointment_date
    FROM appointment a
    JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
    WHERE c.caregiving_type = 'babysitter';
    """
    execute_and_display(query3, "5.3 Work Hours for Babysitter Appointments")
    
    # 5.4 Members in Astana looking for elderly care with no pets rule
    query4 = """
    SELECT DISTINCT u.user_id, u.given_name, u.surname, u.city, m.house_rules
    FROM "user" u
    JOIN member m ON u.user_id = m.member_user_id
    JOIN job j ON m.member_user_id = j.member_user_id
    WHERE j.required_caregiving_type = 'elderly care'
      AND u.city = 'Astana'
      AND m.house_rules LIKE '%No pets%';
    """
    execute_and_display(query4, "5.4 Members in Astana Looking for Elderly Care with 'No pets' Rule")
    
    # Complex queries
    print_separator("6. COMPLEX QUERIES")
    
    # 6.1 Count applicants per job
    query5 = """
    SELECT 
        j.job_id,
        u.given_name || ' ' || u.surname AS member_name,
        COUNT(ja.caregiver_user_id) AS applicant_count
    FROM job j
    JOIN member m ON j.member_user_id = m.member_user_id
    JOIN "user" u ON m.member_user_id = u.user_id
    LEFT JOIN job_application ja ON j.job_id = ja.job_id
    GROUP BY j.job_id, u.given_name, u.surname
    ORDER BY j.job_id;
    """
    execute_and_display(query5, "6.1 Number of Applicants for Each Job")
    
    # 6.2 Total hours by caregivers
    query6 = """
    SELECT 
        c.caregiver_user_id,
        u.given_name || ' ' || u.surname AS caregiver_name,
        SUM(a.work_hours) AS total_hours
    FROM appointment a
    JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN "user" u ON c.caregiver_user_id = u.user_id
    WHERE a.status = 'confirmed'
    GROUP BY c.caregiver_user_id, u.given_name, u.surname
    ORDER BY total_hours DESC;
    """
    execute_and_display(query6, "6.2 Total Hours by Caregivers (Confirmed Appointments)")
    
    # 6.3 Average pay
    query7 = """
    SELECT 
        AVG(c.hourly_rate * a.work_hours) AS average_pay
    FROM appointment a
    JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
    WHERE a.status = 'confirmed';
    """
    execute_and_display(query7, "6.3 Average Pay for Caregivers")
    
    # 6.4 Caregivers earning above average
    query8 = """
    WITH avg_earnings AS (
        SELECT AVG(c.hourly_rate * a.work_hours) AS avg_pay
        FROM appointment a
        JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
        WHERE a.status = 'confirmed'
    )
    SELECT 
        c.caregiver_user_id,
        u.given_name || ' ' || u.surname AS caregiver_name,
        SUM(c.hourly_rate * a.work_hours) AS total_earnings
    FROM appointment a
    JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN "user" u ON c.caregiver_user_id = u.user_id
    CROSS JOIN avg_earnings ae
    WHERE a.status = 'confirmed'
    GROUP BY c.caregiver_user_id, u.given_name, u.surname, ae.avg_pay
    HAVING SUM(c.hourly_rate * a.work_hours) > ae.avg_pay
    ORDER BY total_earnings DESC;
    """
    execute_and_display(query8, "6.4 Caregivers Earning Above Average")
    
    # Derived attribute
    print_separator("7. QUERY WITH DERIVED ATTRIBUTE")
    
    # Calculate total cost
    query9 = """
    SELECT 
        a.appointment_id,
        u.given_name || ' ' || u.surname AS caregiver_name,
        m.given_name || ' ' || m.surname AS member_name,
        a.appointment_date,
        a.work_hours,
        c.hourly_rate,
        (c.hourly_rate * a.work_hours) AS total_cost
    FROM appointment a
    JOIN caregiver c ON a.caregiver_user_id = c.caregiver_user_id
    JOIN "user" u ON c.caregiver_user_id = u.user_id
    JOIN "user" m ON a.member_user_id = m.user_id
    WHERE a.status = 'confirmed'
    ORDER BY a.appointment_id;
    """
    execute_and_display(query9, "7. Total Cost for Confirmed Appointments")
    
    # View operation
    print_separator("8. VIEW OPERATION")
    
    # Create view
    create_view = """
    CREATE OR REPLACE VIEW job_applications_view AS
    SELECT 
        ja.job_id,
        j.required_caregiving_type,
        j.other_requirements,
        ja.date_applied,
        ja.caregiver_user_id,
        u.given_name || ' ' || u.surname AS applicant_name,
        c.caregiving_type,
        c.hourly_rate,
        u.city AS applicant_city
    FROM job_application ja
    JOIN job j ON ja.job_id = j.job_id
    JOIN caregiver c ON ja.caregiver_user_id = c.caregiver_user_id
    JOIN "user" u ON c.caregiver_user_id = u.user_id;
    """
    
    try:
        session.execute(text(create_view))
        session.commit()
        print("View created successfully!\n")
    except Exception as e:
        print(f"Error creating view: {e}\n")
        session.rollback()
    
    # Query the view
    view_query = """
    SELECT * FROM job_applications_view
    ORDER BY job_id, date_applied;
    """
    execute_and_display(view_query, "8. View: Job Applications and Applicants")
    
    print("\n" + "="*80)
    print("  All queries completed!")
    print("="*80 + "\n")
    
    session.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nDatabase connection error: {e}")
        print("\nMake sure:")
        print("1. PostgreSQL is running")
        print("2. Database 'caregivers_db' exists")
        print("3. Tables are created (run schema.sql)")
        print("4. Data is inserted (run insert_data.sql)")
        print("5. Database password is correct")
        session.close()
