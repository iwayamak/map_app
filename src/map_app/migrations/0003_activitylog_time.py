from django.db import migrations, models
import map_app.base_models


class Migration(migrations.Migration):
    dependencies = [
        ("map_app", "0002_state_rename_core_tables"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AddField(
                    model_name="activitylog",
                    name="time",
                    field=models.TimeField(blank=True, null=True, verbose_name="記録時刻"),
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="activitylog",
                    name="time",
                    field=models.TimeField(
                        blank=True,
                        default=map_app.base_models.default_activity_log_time,
                        null=True,
                        verbose_name="記録時刻",
                    ),
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name="activitylog",
            options={
                "ordering": ["-date", "-time", "-created_at"],
                "verbose_name": "記録",
                "verbose_name_plural": "記録",
            },
        ),
    ]
