"""
BULK STUDENT DATA SUMMARY
=========================

Date Created: April 13, 2026
Total Students Added: 634

DEPARTMENT BREAKDOWN
====================

1. Computer Science & Engineering (CSE)
   - Students: 132
   - Status: Ready for face recognition enrollment
   - Allocation: 20.8% of total

2. Civil Engineering
   - Students: 110
   - Status: Ready for face recognition enrollment
   - Allocation: 17.4% of total

3. Information Science
   - Students: 141
   - Status: Ready for face recognition enrollment
   - Allocation: 22.2% of total

4. Mechanical Engineering
   - Students: 147
   - Status: Ready for face recognition enrollment
   - Allocation: 23.2% of total

5. Aeronautical Engineering
   - Students: 104
   - Status: Ready for face recognition enrollment
   - Allocation: 16.4% of total

TOTAL: 634 students
========================================

DATA FIELDS FOR EACH STUDENT
=============================

- name: Randomly generated from list of 250+ Indian first and last names
- email: Auto-generated based on name + random number (format: firstname.lastname[number]@attendance.edu)
- phone_number: Randomly generated 10-digit Indian mobile format (98XXXXXXXX)
- student_class: Department name
- authorized: False (default) - requires admin authorization for face recognition
- image: Empty - students need to upload face images

USAGE
=====

To load this data:

1. If database is empty:
   python manage.py migrate
   python manage.py add_bulk_students

2. To add more students:
   python manage.py add_bulk_students --count 1000
   (This will add 1000 total students distributed equally among departments)

MANAGEMENT COMMAND
==================

Command: add_bulk_students

Features:
- Bulk creates students using Django's bulk_create() for performance
- Generates realistic random data
- Distributed equally (or randomly 100-150) per department
- Batch processing for database efficiency (batch_size=50)
- Progress feedback during creation

Usage:
- python manage.py add_bulk_students              # Random 100-150 per department
- python manage.py add_bulk_students --count 500  # Distribute 500 among departments

Command Location: app1/management/commands/add_bulk_students.py

DATA GENERATION PROCESS
=======================

1. Names: Random selection from 250+ Indian names (first + last)
2. Emails: firstname.lastname[random_number]@attendance.edu
   - Ensures unique emails for each student
   - Professional format for institution

3. Phone Numbers: 98XXXXXXXX (Indian format)
   - Realistic mobile number format
   - Unique random numbers

4. Department: Randomly assigned from 5 departments
   - Equal distribution (100-150 per dept)
   - Can be customized via --count parameter

SECURITY NOTES
==============

- All students created with authorized=False
- Admin must authorize each student for face recognition
- Images must be uploaded separately by students
- Email format does not require validation of real email addresses
- Phone numbers are randomly generated

NEXT STEPS
==========

1. Authorize students:
   - Admin panel: /admin/app1/student/
   - Select students and change authorized=True
   - Or use bulk authorization feature

2. Capture student face images:
   - Students upload via /capture_student/
   - Face encoding stored in database

3. Start attendance system:
   - Access /capture_and_recognize/
   - System will recognize authorized students

DATABASE STATISTICS
===================

Total Records: 634
Table: app1_student

Query to count students:
- SELECT COUNT(*) FROM app1_student;
- SELECT student_class, COUNT(*) FROM app1_student GROUP BY student_class;

API ENDPOINTS FOR STUDENTS
==========================

- GET  /api/v1/students/                 # List all students
- POST /api/v1/students/                 # Create new student
- GET  /api/v1/students/{id}/            # Get specific student
- GET  /api/v1/students/summary/         # Department summary
- GET  /api/v1/students/?search=name     # Search students
- GET  /api/v1/students/?authorized=true # Filter by auth status

SAMPLE STUDENT DATA
===================

Example student record:
{
    "id": 1,
    "name": "Rajesh Kumar",
    "email": "rajesh.kumar1234@attendance.edu",
    "phone_number": "9876543210",
    "student_class": "CSE",
    "authorized": false,
    "image": null
}

TROUBLESHOOTING
===============

Error: "no such table: app1_student"
Solution: Run migrations first
  python manage.py migrate

Error: "unique constraint failed: app1_student.email"
Solution: Emails are unique. If re-running script, delete existing students first:
  python manage.py shell
  >>> from app1.models import Student
  >>> Student.objects.all().delete()

Performance: Bulk insertion takes ~10-30 seconds for 600+ records
- Uses batch_create() for efficiency
- Processes 50 records at a time

FILES CREATED
=============

- app1/management/__init__.py
- app1/management/commands/__init__.py  
- app1/management/commands/add_bulk_students.py (Main command - 150+ lines)

Commit: 885a89d
Message: "Add bulk student management command with random data generation (634 students across 5 departments)"

FUTURE ENHANCEMENTS
===================

1. Add real image generation (PIL/Pillow) for placeholder face images
2. Batch authorization feature in admin
3. CSV export of student data
4. Custom name list per institution
5. Realistic student ID generation
6. Automatic email validation and university email format
7. Attendance pattern generation for testing
8. Role-based student groups

END OF SUMMARY
"""
