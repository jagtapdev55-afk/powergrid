from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='lat',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='lng',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
