from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Sync proxy/concrete permissions between app labels by (model, codename). "
        "Defaults to dry-run; use --execute to apply."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-app-label",
            default="piano_map",
            help="Source app_label to read existing permissions from. Default: piano_map",
        )
        parser.add_argument(
            "--target-app-label",
            default="map_app",
            help="Target app_label to add matching permissions to. Default: map_app",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Actually add missing target permissions to groups/users.",
        )

    def handle(self, *args, **options):
        source_app_label = options["source_app_label"]
        target_app_label = options["target_app_label"]
        execute = bool(options["execute"])

        source_permissions = Permission.objects.filter(
            content_type__app_label=source_app_label
        ).select_related("content_type")
        target_permissions = Permission.objects.filter(
            content_type__app_label=target_app_label
        ).select_related("content_type")

        target_by_key = {
            (perm.content_type.model, perm.codename): perm for perm in target_permissions
        }

        mapped_pairs = []
        missing_targets = []
        for source_perm in source_permissions:
            key = (source_perm.content_type.model, perm_codename_target(source_perm.codename, source_perm.content_type.model))
            target_perm = target_by_key.get(key)
            if target_perm:
                mapped_pairs.append((source_perm, target_perm))
            else:
                missing_targets.append(source_perm)

        group_additions = 0
        user_additions = 0

        for source_perm, target_perm in mapped_pairs:
            groups = Group.objects.filter(permissions=source_perm)
            for group in groups:
                if not group.permissions.filter(pk=target_perm.pk).exists():
                    group_additions += 1
                    if execute:
                        group.permissions.add(target_perm)

            users = User.objects.filter(user_permissions=source_perm)
            for user in users:
                if not user.user_permissions.filter(pk=target_perm.pk).exists():
                    user_additions += 1
                    if execute:
                        user.user_permissions.add(target_perm)

        self.stdout.write(
            "source_app={source} target_app={target} source_permissions={source_count} "
            "mapped={mapped} missing_target={missing}".format(
                source=source_app_label,
                target=target_app_label,
                source_count=source_permissions.count(),
                mapped=len(mapped_pairs),
                missing=len(missing_targets),
            )
        )
        self.stdout.write(
            f"planned_group_additions={group_additions} planned_user_additions={user_additions}"
        )

        if missing_targets:
            sample = ", ".join(
                f"{perm.content_type.model}.{perm.codename}" for perm in missing_targets[:10]
            )
            self.stdout.write(f"missing_target_samples={sample}")

        if not execute:
            self.stdout.write("Dry-run only. Re-run with --execute to apply.")
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Applied additions: groups={group_additions} users={user_additions}"
            )
        )


def perm_codename_target(codename, model_name):
    for action in ("add", "change", "delete", "view"):
        prefix = f"{action}_"
        if codename.startswith(prefix):
            return f"{action}_{model_name}"
    return codename
