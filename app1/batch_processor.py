"""
Advanced batch processing service for efficient bulk operations
Handles large-scale data processing with progress tracking and error recovery
"""

from app1.models import Student, Attendance
from django.db.models import Q, F
from datetime import date, timedelta
import logging
from typing import List, Dict, Callable

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Service for processing large datasets in batches"""

    BATCH_SIZE = 100
    MAX_RETRIES = 3

    @staticmethod
    def process_students_batch(
        queryset,
        process_func: Callable,
        batch_size: int = BATCH_SIZE,
        progress_callback: Callable = None
    ) -> Dict[str, int]:
        """
        Process students in batches with error recovery
        
        Args:
            queryset: Student queryset to process
            process_func: Function to apply to each student
            batch_size: Number of records per batch
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with success/failure counts
        """
        total_count = queryset.count()
        success_count = 0
        failed_count = 0
        error_log = []

        try:
            for batch_num in range(0, total_count, batch_size):
                batch = queryset[batch_num:batch_num + batch_size]

                for student in batch:
                    retry_count = 0
                    while retry_count < BatchProcessor.MAX_RETRIES:
                        try:
                            process_func(student)
                            success_count += 1
                            break
                        except Exception as e:
                            retry_count += 1
                            if retry_count >= BatchProcessor.MAX_RETRIES:
                                failed_count += 1
                                error_log.append({
                                    'student_id': student.id,
                                    'error': str(e)
                                })
                                logger.error(f"Failed to process student {student.id}: {str(e)}")
                            else:
                                logger.warning(
                                    f"Retry {retry_count} for student {student.id}"
                                )

                if progress_callback:
                    progress_callback(
                        current=batch_num + len(batch),
                        total=total_count,
                        success=success_count,
                        failed=failed_count
                    )

            return {
                'total': total_count,
                'success': success_count,
                'failed': failed_count,
                'errors': error_log
            }
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            return {
                'total': total_count,
                'success': success_count,
                'failed': failed_count,
                'errors': error_log,
                'critical_error': str(e)
            }

    @staticmethod
    def authorize_students_batch(
        department: str = None,
        max_count: int = None,
        progress_callback: Callable = None
    ) -> Dict[str, int]:
        """Batch authorize students"""
        queryset = Student.objects.filter(authorized=False)

        if department:
            queryset = queryset.filter(student_class__icontains=department)

        if max_count:
            queryset = queryset[:max_count]

        return BatchProcessor.process_students_batch(
            queryset,
            lambda s: s.update(authorized=True),
            progress_callback=progress_callback
        )

    @staticmethod
    def send_notifications_batch(
        notification_type: str,
        authorized_only: bool = False,
        department: str = None,
        progress_callback: Callable = None
    ) -> Dict[str, int]:
        """Batch send notifications"""
        from app1.notification_service import EmailNotificationService

        queryset = Student.objects.all()

        if authorized_only:
            queryset = queryset.filter(authorized=True)

        if department:
            queryset = queryset.filter(student_class__icontains=department)

        def send_notification(student):
            if notification_type == 'reminder':
                result = EmailNotificationService.send_attendance_reminder(student)
            elif notification_type == 'authorization':
                result = EmailNotificationService.send_student_authorization_notification(student)
            elif notification_type == 'report':
                result = EmailNotificationService.send_attendance_report(student)
            else:
                result = False

            if not result:
                raise Exception(f"Failed to send {notification_type} to {student.email}")

        return BatchProcessor.process_students_batch(
            queryset,
            send_notification,
            progress_callback=progress_callback
        )

    @staticmethod
    def update_attendance_status_batch(
        date_filter: date = None,
        status_update_func: Callable = None,
        progress_callback: Callable = None
    ) -> Dict[str, int]:
        """Batch update attendance records"""
        if not date_filter:
            date_filter = date.today()

        queryset = Attendance.objects.filter(date=date_filter)
        total = queryset.count()
        updated = 0
        failed = 0

        try:
            batch_size = BatchProcessor.BATCH_SIZE

            for batch_num in range(0, total, batch_size):
                batch = list(queryset[batch_num:batch_num + batch_size])

                for record in batch:
                    try:
                        if status_update_func:
                            status_update_func(record)
                        updated += 1
                    except Exception as e:
                        failed += 1
                        logger.error(f"Failed to update attendance {record.id}: {str(e)}")

                if progress_callback:
                    progress_callback(
                        current=min(batch_num + batch_size, total),
                        total=total,
                        success=updated,
                        failed=failed
                    )

            return {
                'total': total,
                'updated': updated,
                'failed': failed
            }
        except Exception as e:
            logger.error(f"Batch update error: {str(e)}")
            return {
                'total': total,
                'updated': updated,
                'failed': failed,
                'error': str(e)
            }

    @staticmethod
    def bulk_export_data(
        export_type: str,
        filters: Dict = None,
        batch_size: int = 1000,
        progress_callback: Callable = None
    ) -> Dict:
        """Bulk export data in batches"""
        from app1.search_service import AttendanceSearchService

        try:
            if export_type == 'attendance':
                queryset = AttendanceSearchService.search_attendance(filters or {})
            elif export_type == 'students':
                queryset = AttendanceSearchService.search_students(
                    "",
                    filters or {}
                )
            else:
                return {'error': f'Unknown export type: {export_type}'}

            total = queryset.count()
            exported = 0

            for batch_num in range(0, total, batch_size):
                batch = list(queryset[batch_num:batch_num + batch_size])
                exported += len(batch)

                if progress_callback:
                    progress_callback(
                        current=exported,
                        total=total,
                        percentage=round(exported / total * 100) if total > 0 else 0
                    )

            return {
                'status': 'completed',
                'export_type': export_type,
                'total_records': total,
                'exported': exported
            }
        except Exception as e:
            logger.error(f"Bulk export error: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    @staticmethod
    def cleanup_duplicate_records() -> Dict[str, int]:
        """Remove duplicate attendance records"""
        try:
            duplicates = Attendance.objects.values(
                'student_id', 'date'
            ).annotate(
                count=Count('id')
            ).filter(
                count__gt=1
            )

            deleted_count = 0

            for dup in duplicates:
                records = Attendance.objects.filter(
                    student_id=dup['student_id'],
                    date=dup['date']
                ).order_by('id')[1:]  # Keep first, delete rest

                count, _ = records.delete()
                deleted_count += count

            logger.info(f"Cleaned up {deleted_count} duplicate records")
            return {
                'status': 'completed',
                'duplicates_found': duplicates.count(),
                'records_deleted': deleted_count
            }
        except Exception as e:
            logger.error(f"Error cleaning duplicates: {str(e)}")
            return {'error': str(e)}

    @staticmethod
    def migrate_data_batch(
        source_model,
        target_model,
        mapping_func: Callable,
        progress_callback: Callable = None
    ) -> Dict:
        """Migrate data from source to target model in batches"""
        try:
            source_data = source_model.objects.all()
            total = source_data.count()
            migrated = 0
            failed = 0
            batch_size = BatchProcessor.BATCH_SIZE

            for batch_num in range(0, total, batch_size):
                batch = list(source_data[batch_num:batch_num + batch_size])

                for record in batch:
                    try:
                        mapping_func(record, target_model)
                        migrated += 1
                    except Exception as e:
                        failed += 1
                        logger.error(f"Migration error: {str(e)}")

                if progress_callback:
                    progress_callback(
                        current=min(batch_num + batch_size, total),
                        total=total,
                        migrated=migrated,
                        failed=failed
                    )

            return {
                'status': 'completed',
                'total': total,
                'migrated': migrated,
                'failed': failed
            }
        except Exception as e:
            logger.error(f"Data migration error: {str(e)}")
            return {'error': str(e)}
