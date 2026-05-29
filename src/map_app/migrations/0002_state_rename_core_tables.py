from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("map_app", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelTable(name="activityitem", table="map_app_activityitem"),
                migrations.AlterModelTable(name="activitylog", table="map_app_activitylog"),
                migrations.AlterModelTable(name="activitylogitem", table="map_app_activitylogitem"),
                migrations.AlterModelTable(name="domainfielddefinition", table="map_app_domainfielddefinition"),
                migrations.AlterModelTable(name="location", table="map_app_location"),
                migrations.AlterModelTable(name="locationphoto", table="map_app_locationphoto"),
                migrations.AlterModelTable(name="sitesettings", table="map_app_sitesettings"),
                migrations.AlterModelTable(name="tag", table="map_app_tag"),
                migrations.AlterModelTable(name="video", table="map_app_video"),
                migrations.AlterField(
                    model_name="location",
                    name="tags",
                    field=models.ManyToManyField(
                        blank=True,
                        db_table="map_app_location_tags",
                        related_name="locations",
                        to="map_app.tag",
                        verbose_name="タグ",
                    ),
                ),
            ],
        ),
    ]
