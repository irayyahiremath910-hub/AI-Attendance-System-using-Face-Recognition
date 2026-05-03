"""
Advanced report generation system
Creates, schedules, and distributes reports in multiple formats
"""

from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging
import json
from enum import Enum

logger = logging.getLogger(__name__)


class ReportType(Enum):
    """Report types"""

    ATTENDANCE = 'attendance'
    ANALYTICS = 'analytics'
    COMPLIANCE = 'compliance'
    PERFORMANCE = 'performance'
    CUSTOM = 'custom'


class ReportFrequency(Enum):
    """Report generation frequency"""

    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    ANNUAL = 'annual'
    CUSTOM = 'custom'


class ReportFormat(Enum):
    """Report output formats"""

    PDF = 'pdf'
    EXCEL = 'excel'
    JSON = 'json'
    CSV = 'csv'
    HTML = 'html'


class ReportBuilder(ABC):
    """Base class for report builders"""

    def __init__(self, report_name, report_type):
        self.report_name = report_name
        self.report_type = report_type
        self.data = {}
        self.metadata = {
            'created_at': datetime.now(),
            'title': report_name,
            'type': report_type.value,
        }

    @abstractmethod
    def build(self):
        """Build report"""
        pass

    @abstractmethod
    def validate(self):
        """Validate report data"""
        pass


class AttendanceReportBuilder(ReportBuilder):
    """Build attendance reports"""

    def __init__(self, start_date, end_date):
        super().__init__('Attendance Report', ReportType.ATTENDANCE)
        self.start_date = start_date
        self.end_date = end_date

    def build(self):
        """Build attendance report"""
        self.data = {
            'period': f"{self.start_date} to {self.end_date}",
            'summary': {
                'total_students': 0,
                'total_days': 0,
                'average_attendance': 0,
            },
            'daily_breakdown': [],
            'student_breakdown': [],
        }
        return self.data

    def validate(self):
        """Validate report"""
        return (
            self.start_date and self.end_date and
            self.start_date <= self.end_date
        )


class AnalyticsReportBuilder(ReportBuilder):
    """Build analytics reports"""

    def __init__(self):
        super().__init__('Analytics Report', ReportType.ANALYTICS)

    def build(self):
        """Build analytics report"""
        self.data = {
            'trends': [],
            'patterns': [],
            'insights': [],
            'recommendations': [],
            'metrics': {},
        }
        return self.data

    def validate(self):
        """Validate analytics report"""
        return len(self.data) > 0


class ComplianceReportBuilder(ReportBuilder):
    """Build compliance reports"""

    def __init__(self):
        super().__init__('Compliance Report', ReportType.COMPLIANCE)

    def build(self):
        """Build compliance report"""
        self.data = {
            'compliance_checks': [],
            'violations': [],
            'remediation_actions': [],
            'compliance_score': 0,
        }
        return self.data

    def validate(self):
        """Validate compliance report"""
        return 'compliance_checks' in self.data


class ReportSchedule:
    """Schedule for report generation"""

    def __init__(self, report_id, frequency, recipients, enabled=True):
        self.report_id = report_id
        self.frequency = frequency
        self.recipients = recipients
        self.enabled = enabled
        self.next_run = self._calculate_next_run()
        self.last_run = None

    def _calculate_next_run(self):
        """Calculate next run time"""
        now = datetime.now()

        if self.frequency == ReportFrequency.DAILY:
            return now + timedelta(days=1)
        elif self.frequency == ReportFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        elif self.frequency == ReportFrequency.MONTHLY:
            return now + timedelta(days=30)
        else:
            return now + timedelta(days=1)

    def should_run(self):
        """Check if schedule should run"""
        return self.enabled and datetime.now() >= self.next_run

    def mark_run(self):
        """Mark schedule as run"""
        self.last_run = datetime.now()
        self.next_run = self._calculate_next_run()


class ReportRenderer:
    """Render reports in different formats"""

    @staticmethod
    def render_json(report_data, metadata):
        """Render as JSON"""
        return json.dumps({
            'metadata': metadata,
            'data': report_data,
        }, indent=2, default=str)

    @staticmethod
    def render_csv(report_data, metadata):
        """Render as CSV"""
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Write metadata
        for key, value in metadata.items():
            writer.writerow([key, value])

        writer.writerow([])  # Empty row

        # Write data headers
        if isinstance(report_data, dict):
            writer.writerow(report_data.keys())
            if report_data:
                first_value = next(iter(report_data.values()))
                if isinstance(first_value, (list, tuple)):
                    for row in first_value:
                        writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def render_html(report_data, metadata):
        """Render as HTML"""
        html = "<html><head><style>"
        html += "body { font-family: Arial; margin: 20px; }"
        html += "table { border-collapse: collapse; width: 100%; }"
        html += "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }"
        html += "th { background-color: #4CAF50; color: white; }"
        html += "</style></head><body>"

        # Add metadata
        html += "<h1>" + metadata.get('title', 'Report') + "</h1>"
        html += f"<p>Generated: {metadata.get('created_at', 'N/A')}</p>"

        # Add data table
        html += "<table>"
        if isinstance(report_data, dict):
            for key, value in report_data.items():
                html += f"<tr><th>{key}</th><td>{value}</td></tr>"
        html += "</table>"
        html += "</body></html>"

        return html

    @staticmethod
    def render_pdf(report_data, metadata):
        """Render as PDF"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors

            pdf_content = f"Report: {metadata.get('title', 'Report')}\n"
            pdf_content += f"Generated: {metadata.get('created_at', 'N/A')}\n\n"
            pdf_content += json.dumps(report_data, indent=2, default=str)

            return pdf_content
        except ImportError:
            logger.error("reportlab not installed for PDF generation")
            return None


class ReportGenerator:
    """Main report generator service"""

    def __init__(self):
        self.schedules = {}
        self.generated_reports = []
        self.report_count = 0

    def create_report(self, builder: ReportBuilder, format=ReportFormat.PDF):
        """Create and render report"""
        try:
            if not builder.validate():
                logger.error(f"Report validation failed: {builder.report_name}")
                return None

            report_data = builder.build()
            renderer = ReportRenderer()

            if format == ReportFormat.JSON:
                content = renderer.render_json(report_data, builder.metadata)
            elif format == ReportFormat.CSV:
                content = renderer.render_csv(report_data, builder.metadata)
            elif format == ReportFormat.HTML:
                content = renderer.render_html(report_data, builder.metadata)
            elif format == ReportFormat.PDF:
                content = renderer.render_pdf(report_data, builder.metadata)
            else:
                return None

            self.report_count += 1
            report = {
                'id': self.report_count,
                'name': builder.report_name,
                'format': format.value,
                'content': content,
                'metadata': builder.metadata,
                'created_at': datetime.now(),
            }

            self.generated_reports.append(report)
            logger.info(f"Report generated: {builder.report_name} ({format.value})")
            return report

        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            return None

    def schedule_report(self, report_id, schedule: ReportSchedule):
        """Schedule report generation"""
        self.schedules[report_id] = schedule
        logger.info(f"Report scheduled: {report_id}")

    def process_scheduled_reports(self):
        """Process all scheduled reports"""
        processed = []
        for report_id, schedule in self.schedules.items():
            if schedule.should_run():
                schedule.mark_run()
                processed.append(report_id)
                logger.info(f"Processing scheduled report: {report_id}")

        return processed

    def get_report(self, report_id):
        """Get generated report"""
        for report in self.generated_reports:
            if report['id'] == report_id:
                return report
        return None

    def get_reports_by_type(self, report_type):
        """Get reports by type"""
        return [r for r in self.generated_reports if r['metadata']['type'] == report_type.value]

    def archive_old_reports(self, days=30):
        """Archive reports older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        archived = []
        remaining = []

        for report in self.generated_reports:
            if report['created_at'] < cutoff_date:
                archived.append(report['id'])
            else:
                remaining.append(report)

        self.generated_reports = remaining
        logger.info(f"Archived {len(archived)} old reports")
        return archived

    def export_reports(self, format=ReportFormat.CSV):
        """Export all reports metadata"""
        exports = []
        for report in self.generated_reports:
            exports.append({
                'id': report['id'],
                'name': report['name'],
                'format': report['format'],
                'created_at': report['created_at'].isoformat(),
            })

        if format == ReportFormat.JSON:
            return json.dumps(exports, indent=2)
        else:
            return exports


# Global report generator
global_report_generator = ReportGenerator()
