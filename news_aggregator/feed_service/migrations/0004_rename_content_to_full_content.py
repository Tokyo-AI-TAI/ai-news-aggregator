# Generated by Django 5.0.9 on 2024-12-14 03:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed_service', '0003_feed_feed_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feedentry',
            name='content',
        ),
        migrations.AddField(
            model_name='feedentry',
            name='article_load_error',
            field=models.TextField(blank=True, default='', help_text='Error message if article loading failed'),
        ),
        migrations.AddField(
            model_name='feedentry',
            name='article_loaded_at',
            field=models.DateTimeField(blank=True, help_text='When the full article was loaded', null=True),
        ),
        migrations.AddField(
            model_name='feedentry',
            name='full_content',
            field=models.TextField(default='', help_text='Full content of the article. Initially contains feed summary, later updated with full article text'),
            preserve_default=False,
        ),
    ]
