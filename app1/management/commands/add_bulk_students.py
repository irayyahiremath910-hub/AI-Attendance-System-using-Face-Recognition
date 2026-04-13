"""
Django management command to bulk add students with random data.

Usage:
    python manage.py add_bulk_students
"""

from django.core.management.base import BaseCommand
from app1.models import Student
import random
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Bulk add students with random data across departments'

    # First names for generating random names
    FIRST_NAMES = [
        'Aarav', 'Abhishek', 'Aditya', 'Akshay', 'Amit', 'Anand', 'Aniket', 'Ankit', 'Anmol', 'Anurag',
        'Arjun', 'Arpit', 'Ashish', 'Ashok', 'Avanish', 'Ayush', 'Bhavin', 'Bhavesh', 'Bhupendra', 'Bipin',
        'Darshan', 'Deepak', 'Dhaval', 'Dheeraj', 'Dhruv', 'Dileep', 'Dinesh', 'Divyanshu', 'Divyesh', 'Dushyant',
        'Gagan', 'Garima', 'Gaurav', 'Gautam', 'Girish', 'Gokul', 'Govind', 'Gyan', 'Harendra', 'Harish',
        'Harman', 'Harsh', 'Hemant', 'Hukum', 'Hussain', 'Ishan', 'Ishwar', 'Iti', 'Jagjit', 'Jagmohan',
        'Jahangir', 'Jahir', 'Jai', 'Jainendra', 'Jaipal', 'Jaiswal', 'Jaitendra', 'Jal', 'Jalin', 'Jalinder',
        'Jameel', 'Jamil', 'Janak', 'Janardhan', 'Janendra', 'Janier', 'Janin', 'Janish', 'Janita', 'Janki',
        'Jaran', 'Jarasandha', 'Jarbhara', 'Jari', 'Jaripat', 'Jarling', 'Jarman', 'Jaroo', 'Jarpat', 'Jasleen',
        'Jasmer', 'Jasmijn', 'Jasmine', 'Jason', 'Jass', 'Jaswandan', 'Jaswin', 'Jaswinder', 'Jatendra', 'Jatin',
        'Kadam', 'Kailash', 'Kairav', 'Kairon', 'Kaist', 'Kaivalya', 'Kajol', 'Kala', 'Kalap', 'Kalash',
        'Kalervo', 'Kalidas', 'Kalim', 'Kalinath', 'Kalinich', 'Kalindi', 'Kalindi', 'Kalini', 'Kalio', 'Kalip',
        'Krishna', 'Krishan', 'Krisnan', 'Krish', 'Krisna', 'Krisson', 'Kristian', 'Kristin', 'Kronos', 'Krushna',
        'Lakhan', 'Lakshman', 'Lakshmi', 'Lakshya', 'Lalendra', 'Lalith', 'Lalitmohan', 'Lall', 'Lallu', 'Lalmani',
        'Maahir', 'Maalik', 'Manas', 'Manav', 'Manbir', 'Mandip', 'Maneesh', 'Manerji', 'Mangal', 'Mangesh',
        'Nikesh', 'Nikhil', 'Nikhilesh', 'Nikita', 'Nikki', 'Nikul', 'Nilendra', 'Nilesh', 'Niles', 'Nili',
        'Ompal', 'Omri', 'Omprakash', 'Omprasad', 'Ompratap', 'Omrao', 'Omveer', 'Onkar', 'Onkareshwar', 'Onkarkumar',
        'Paban', 'Pabitra', 'Pachar', 'Pachappa', 'Pachen', 'Pacher', 'Pacholia', 'Pacho', 'Pachom', 'Pachomius',
        'Rajesh', 'Rajeev', 'Rajendra', 'Rajesh', 'Rajinder', 'Rajkumar', 'Rajkumari', 'Rajnish', 'Rajnath', 'Rajpal',
        'Sameer', 'Samit', 'Samith', 'Samja', 'Samjhta', 'Sammit', 'Sammits', 'Sampath', 'Sampat', 'Samrat',
        'Taaraka', 'Taarif', 'Taavish', 'Tabar', 'Tabinas', 'Tabish', 'Tabor', 'Taboris', 'Tabuk', 'Tabuti',
        'Umer', 'Umesh', 'Umid', 'Umid', 'Umina', 'Uminn', 'Umit', 'Umitay', 'Umithalion', 'Umitosh',
        'Vedavyas', 'Vedendra', 'Vedhavati', 'Vedhayu', 'Vedic', 'Vedipal', 'Vedpal', 'Vedraj', 'Vedrum', 'Veena',
        'Vikram', 'Vikrant', 'Vikrama', 'Vikramadevi', 'Vikramendra', 'Vikramjit', 'Vikramjot', 'Vikramkumar', 'Vikramraj', 'Vikramen',
        'Vivaan', 'Vivaha', 'Vivaj', 'Vivaiji', 'Vivaran', 'Vivart', 'Vivata', 'Vivekananda', 'Vivekanandha', 'Vivekansh',
        'Wrishi', 'Wrist', 'Wristin', 'Wristya', 'Writesh', 'Writhak', 'Writhama', 'Writhikesh', 'Writhis', 'Writam',
        'Yagat', 'Yagendra', 'Yagi', 'Yagmur', 'Yagna', 'Yagnapal', 'Yagnaraj', 'Yagnaraja', 'Yagnarishi', 'Yagnashree',
        'Zain', 'Zainal', 'Zainald', 'Zainar', 'Zainash', 'Zaind', 'Zainka', 'Zainkaran', 'Zainkesh', 'Zainulla',
    ]

    LAST_NAMES = [
        'Kumar', 'Singh', 'Patel', 'Verma', 'Sharma', 'Gupta', 'Rao', 'Reddy', 'Pandey', 'Mishra',
        'Nair', 'Iyer', 'Menon', 'Desai', 'Joshi', 'Bhat', 'Amin', 'Khan', 'Siddiqui', 'Ahmed',
        'Hassan', 'Al-Hakim', 'Hussain', 'Ali', 'Mohammad', 'Malik', 'Razi', 'Saha', 'Banerjee', 'Chatterjee',
        'Mukherjee', 'Roy', 'Dutta', 'Sen', 'Ghosh', 'Bose', 'Mazumdar', 'Sinha', 'Das', 'Chandra',
        'Dey', 'Bhatia', 'Chopra', 'Khanna', 'Malhotra', 'Arora', 'Anand', 'Asthana', 'Bhattacharya', 'Choudhary',
    ]

    DEPARTMENTS = ['CSE', 'Civil', 'Information Science', 'Mechanical', 'Aeronautical']

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=None,
            help='Total students to add (will divide among departments). If not specified, random 100-150 per dept'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting bulk student addition...'))
        
        departments = self.DEPARTMENTS
        total_added = 0
        
        for department in departments:
            # Random count between 100-150 students per department
            if options['count']:
                count = options['count'] // len(departments)
            else:
                count = random.randint(100, 150)
            
            self.stdout.write(f'\nAdding {count} students to {department}...')
            
            students_to_create = []
            
            for i in range(count):
                first_name = random.choice(self.FIRST_NAMES)
                last_name = random.choice(self.LAST_NAMES)
                name = f"{first_name} {last_name}"
                
                # Generate email from name
                email_base = f"{first_name.lower()}.{last_name.lower()}{random.randint(100, 9999)}"
                email = f"{email_base}@attendance.edu"
                
                # Generate random phone number
                phone = f"98{random.randint(10000000, 99999999)}"
                
                # Class is the department name
                student_class = department
                
                student = Student(
                    name=name,
                    email=email,
                    phone_number=phone,
                    student_class=student_class,
                    authorized=False
                )
                
                students_to_create.append(student)
            
            # Bulk create students
            created_students = Student.objects.bulk_create(students_to_create, batch_size=50)
            total_added += len(created_students)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Added {len(created_students)} students to {department}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully added {total_added} students total across all departments!'))
        
        # Print summary
        for department in departments:
            count = Student.objects.filter(student_class=department).count()
            self.stdout.write(f'  • {department}: {count} students')
