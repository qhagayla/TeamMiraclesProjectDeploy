# Generated by Django 4.0.8 on 2023-11-07 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('result', '0005_alter_result_id_alter_takencourse_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='status',
            field=models.CharField(choices=[('Regular', 'Regular Student'), ('Irregular', 'Irregular Student')], max_length=25, null=True),
        ),
    ]
