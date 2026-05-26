import csv
from datetime import datetime

from django.db import IntegrityError


def import_activity_log_csv(
    *,
    csv_file,
    clear_data=False,
    stdout,
    style,
    activity_item_model,
    activity_log_model,
    activity_log_item_model,
    location_model,
):
    if clear_data:
        stdout.write(style.WARNING("Clearing existing data..."))
        activity_log_item_model.objects.all().delete()
        activity_log_model.objects.all().delete()
        location_model.objects.all().delete()
        activity_item_model.objects.all().delete()
        stdout.write(style.SUCCESS("Data cleared."))

    location_cache = {}
    item_cache = {}

    created_locations = 0
    updated_locations = 0
    created_activity_logs = 0
    updated_activity_logs = 0
    created_activity_items = 0
    linked_activity_items = 0
    skipped_rows = 0

    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row_num, row in enumerate(reader, start=2):
            try:
                if not row.get("場所") or not row.get("日付"):
                    stdout.write(
                        style.WARNING(f"Row {row_num}: Missing required fields (場所 or 日付), skipping")
                    )
                    skipped_rows += 1
                    continue

                location_name = row["場所"].strip()
                date_str = row["日付"].strip()
                latitude = row.get("緯度", "").strip()
                longitude = row.get("経度", "").strip()

                try:
                    date = datetime.strptime(date_str, "%Y/%m/%d").date()
                except ValueError:
                    stdout.write(style.WARNING(f'Row {row_num}: Invalid date format "{date_str}", skipping'))
                    skipped_rows += 1
                    continue

                lat_value = float(latitude) if latitude else 35.6812
                lon_value = float(longitude) if longitude else 139.7671

                if location_name in location_cache:
                    location = location_cache[location_name]
                else:
                    location, created = location_model.objects.get_or_create(
                        name=location_name,
                        defaults={"latitude": lat_value, "longitude": lon_value},
                    )
                    location_cache[location_name] = location
                    if created:
                        created_locations += 1
                    elif location.latitude != lat_value or location.longitude != lon_value:
                        location.latitude = lat_value
                        location.longitude = lon_value
                        location.save(update_fields=["latitude", "longitude"])
                        updated_locations += 1

                item_names = []
                for i in range(1, 14):
                    item_key = f"曲名{i}"
                    if item_key in row and row[item_key].strip():
                        item_names.append(row[item_key].strip())

                unique_item_names = []
                seen = set()
                for item_name in item_names:
                    if item_name not in seen:
                        seen.add(item_name)
                        unique_item_names.append(item_name)

                activity_log = activity_log_model.objects.create(
                    location=location,
                    date=date,
                    title=", ".join(unique_item_names),
                )
                created_activity_logs += 1

                for order, item_name in enumerate(unique_item_names):
                    if item_name in item_cache:
                        activity_item = item_cache[item_name]
                    else:
                        activity_item, item_created = activity_item_model.objects.get_or_create(name=item_name)
                        item_cache[item_name] = activity_item
                        if item_created:
                            created_activity_items += 1

                    activity_log_item_model.objects.create(
                        activity_log=activity_log,
                        item=activity_item,
                        order=order,
                    )
                    linked_activity_items += 1

            except (KeyError, TypeError, ValueError, IntegrityError) as exc:
                stdout.write(style.ERROR(f"Row {row_num}: Error - {str(exc)}"))
                skipped_rows += 1
                continue

    stdout.write(style.SUCCESS("\n=== Import Summary ==="))
    stdout.write(style.SUCCESS(f"Locations created: {created_locations}"))
    stdout.write(style.SUCCESS(f"Locations updated: {updated_locations}"))
    stdout.write(style.SUCCESS(f"Activity logs created: {created_activity_logs}"))
    stdout.write(style.SUCCESS(f"Activity logs updated: {updated_activity_logs}"))
    stdout.write(style.SUCCESS(f"Activity items created: {created_activity_items}"))
    stdout.write(style.SUCCESS(f"Activity log items linked: {linked_activity_items}"))
    if skipped_rows > 0:
        stdout.write(style.WARNING(f"Rows skipped: {skipped_rows}"))
    stdout.write(style.SUCCESS("\nImport completed successfully!"))
