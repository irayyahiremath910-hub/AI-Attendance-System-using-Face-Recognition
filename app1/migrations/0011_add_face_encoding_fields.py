# Generated migration for face encoding fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0010_remove_cameraconfiguration_success_sound_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='face_encoding',
            field=models.JSONField(blank=True, help_text='Stored face encoding for recognition', null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='face_recognized',
            field=models.BooleanField(default=False, help_text='Whether face has been encoded and ready for recognition'),
        ),
        migrations.AddField(
            model_name='student',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
