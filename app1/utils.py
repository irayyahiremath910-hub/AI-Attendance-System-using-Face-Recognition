import csv
import json
from io import BytesIO
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Count, Q
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

from .models import Student, Attendance, AttendanceSummary


def export_attendance_to_csv(request, start_date=None, end_date=None, student_id=None):
    """Export attendance records to CSV"""
    query = Attendance.objects.select_related('student')
    
    if start_date and end_date:
        query = query.filter(date__range=[start_date, end_date])
    
    if student_id:
        query = query.filter(student_id=student_id)
    
    query = query.order_by('date', 'student__name')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Student Name', 'Student Class', 'Check-In Time', 'Check-Out Time', 'Duration', 'Status'])
    
    for record in query:
        writer.writerow([
            record.date,
            record.student.name,
            record.student.student_class,
            record.check_in_time or 'N/A',
            record.check_out_time or 'N/A',
            record.calculate_duration() or 'N/A',
            record.status,
        ])
    
    return response


def export_attendance_to_pdf(start_date=None, end_date=None, student_id=None):
    """Export attendance records to PDF"""
    query = Attendance.objects.select_related('student')
    
    if start_date and end_date:
        query = query.filter(date__range=[start_date, end_date])
    
    if student_id:
        query = query.filter(student_id=student_id)
    
    query = query.order_by('date', 'student__name')
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=30,
        alignment=1
    )
    
    # Title
    title = Paragraph("Attendance Report", title_style)
    elements.append(title)
    
    # Report date range
    if start_date and end_date:
        date_range = f"Period: {start_date} to {end_date}"
    else:
        date_range = f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    elements.append(Paragraph(date_range, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Data for table
    data = [['Date', 'Student Name', 'Class', 'Check-In', 'Check-Out', 'Duration', 'Status']]
    
    for record in query:
        data.append([
            str(record.date),
            record.student.name,
            record.student.student_class,
            record.check_in_time.strftime('%H:%M') if record.check_in_time else '-',
            record.check_out_time.strftime('%H:%M') if record.check_out_time else '-',
            record.calculate_duration() or '-',
            record.status,
        ])
    
    # Create table
    table = Table(data, colWidths=[1*inch, 1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_report.pdf"'
    
    return response


def get_dashboard_statistics(days=30):
    """Get comprehensive dashboard statistics"""
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    total_students = Student.objects.filter(authorized=True).count()
    total_attendance_records = Attendance.objects.filter(date__range=[start_date, today]).count()
    
    # Attendance by status
    present_count = Attendance.objects.filter(
        date__range=[start_date, today],
        check_in_time__isnull=False
    ).count()
    
    absent_count = Attendance.objects.filter(
        date__range=[start_date, today],
        check_in_time__isnull=True
    ).count()
    
    # Daily average
    attendance_by_date = Attendance.objects.filter(
        date__range=[start_date, today]
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    daily_data = []
    for record in attendance_by_date:
        daily_data.append({
            'date': record['date'].strftime('%Y-%m-%d'),
            'present': Attendance.objects.filter(
                date=record['date'],
                check_in_time__isnull=False
            ).count(),
            'absent': Attendance.objects.filter(
                date=record['date'],
                check_in_time__isnull=True
            ).count(),
        })
    
    # Low attendance students
    low_attendance_students = []
    for student in Student.objects.filter(authorized=True):
        percentage = student.get_attendance_percentage(days)
        if percentage < 75:
            low_attendance_students.append({
                'name': student.name,
                'percentage': round(percentage, 2),
                'email': student.email
            })
    
    # Class-wise statistics
    class_stats = {}
    for student_class in Student.objects.filter(authorized=True).values_list('student_class', flat=True).distinct():
        class_students = Student.objects.filter(student_class=student_class, authorized=True)
        total = class_students.count()
        
        present = Attendance.objects.filter(
            student__in=class_students,
            date__range=[start_date, today],
            check_in_time__isnull=False
        ).count()
        
        percentage = (present / (total * days) * 100) if total > 0 else 0
        
        class_stats[student_class] = {
            'total_students': total,
            'present_count': present,
            'percentage': round(percentage, 2)
        }
    
    return {
        'total_students': total_students,
        'total_records': total_attendance_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'presence_percentage': (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0,
        'daily_data': daily_data,
        'low_attendance_students': low_attendance_students,
        'class_statistics': class_stats,
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d'),
        }
    }


def get_student_report(student_id, days=90):
    """Get detailed report for a specific student"""
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return None
    
    today = timezone.now().date()
    start_date = today - timedelta(days=days)
    
    attendance_records = Attendance.objects.filter(
        student=student,
        date__range=[start_date, today]
    ).order_by('date')
    
    total_days = attendance_records.count()
    present_days = attendance_records.filter(check_in_time__isnull=False).count()
    absent_days = attendance_records.filter(check_in_time__isnull=True).count()
    late_days = attendance_records.filter(status='late').count()
    
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    total_hours = 0
    for record in attendance_records:
        if record.check_in_time and record.check_out_time:
            duration = record.check_out_time - record.check_in_time
            total_hours += duration.total_seconds() / 3600
    
    return {
        'student': {
            'name': student.name,
            'email': student.email,
            'class': student.student_class,
            'authorized': student.authorized,
        },
        'attendance_summary': {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_percentage': round(attendance_percentage, 2),
            'total_hours': round(total_hours, 2),
        },
        'attendance_records': [
            {
                'date': rec.date.strftime('%Y-%m-%d'),
                'check_in': rec.check_in_time.strftime('%H:%M') if rec.check_in_time else None,
                'check_out': rec.check_out_time.strftime('%H:%M') if rec.check_out_time else None,
                'duration': rec.calculate_duration(),
                'status': rec.status,
            }
            for rec in attendance_records
        ],
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': today.strftime('%Y-%m-%d'),
        }
    }
