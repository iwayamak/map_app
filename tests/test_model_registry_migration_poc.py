import subprocess
import sys
import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase


class ModelRegistryMigrationPoCTests(TestCase):
    def _run_django_poc(self, files, script):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for relative_path, content in files.items():
                file_path = temp_path / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(textwrap.dedent(content), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, "-c", textwrap.dedent(script)],
                cwd=temp_path,
                text=True,
                capture_output=True,
                check=False,
            )
            return result

    def test_duplicate_concrete_models_with_same_table_fail_system_check(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
        }
        script = """
            from django.conf import settings
            from django.core.management import call_command
            import django

            settings.configure(
                INSTALLED_APPS=["shared_app", "host_app"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()
            call_command("check", verbosity=0)
        """

        result = self._run_django_poc(files, script)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("models.E028", result.stderr)
        self.assertIn("piano_map_location", result.stderr)

    def test_proxy_wrapper_keeps_host_registry_entry_without_table_duplication(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            from django.core.management import call_command
            import django

            settings.configure(
                INSTALLED_APPS=["shared_app", "host_app"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()
            call_command("check", verbosity=0)

            shared = apps.get_model("shared_app", "Location")
            host = apps.get_model("host_app", "Location")
            assert host._meta.proxy is True
            assert host._meta.db_table == "piano_map_location"
            assert host._meta.concrete_model is shared
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_proxy_wrapper_content_type_depends_on_concrete_model_flag(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            from django.db import connection
            import django

            settings.configure(
                INSTALLED_APPS=["django.contrib.contenttypes", "shared_app", "host_app"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()
            from django.contrib.contenttypes.models import ContentType

            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(ContentType)

            shared = apps.get_model("shared_app", "Location")
            host = apps.get_model("host_app", "Location")

            concrete_ct = ContentType.objects.get_for_model(host)
            proxy_ct = ContentType.objects.get_for_model(host, for_concrete_model=False)
            shared_ct = ContentType.objects.get_for_model(shared)

            assert concrete_ct == shared_ct
            assert concrete_ct.app_label == "shared_app"
            assert concrete_ct.model == "location"
            assert proxy_ct.app_label == "host_app"
            assert proxy_ct.model == "location"
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_direct_alias_does_not_create_host_registry_model(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            import django

            settings.configure(
                INSTALLED_APPS=["shared_app", "host_app"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()

            imported_location = __import__("host_app.models", fromlist=["Location"]).Location
            assert imported_location._meta.app_label == "shared_app"
            try:
                apps.get_model("host_app", "Location")
            except LookupError:
                pass
            else:
                raise AssertionError("direct alias unexpectedly registered host_app.Location")
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_proxy_wrapper_admin_url_permission_and_change_form_work(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
            "host_app/admin.py": """
                from django.contrib import admin
                from .models import Location


                @admin.register(Location)
                class LocationAdmin(admin.ModelAdmin):
                    list_display = ("id", "name")
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            from django.core.management import call_command
            from django.urls import path, reverse
            import django

            settings.configure(
                INSTALLED_APPS=[
                    "django.contrib.admin",
                    "django.contrib.auth",
                    "django.contrib.contenttypes",
                    "django.contrib.sessions",
                    "shared_app",
                    "host_app",
                ],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                ROOT_URLCONF=__name__,
                MIDDLEWARE=[
                    "django.contrib.sessions.middleware.SessionMiddleware",
                    "django.contrib.auth.middleware.AuthenticationMiddleware",
                ],
                TEMPLATES=[
                    {
                        "BACKEND": "django.template.backends.django.DjangoTemplates",
                        "APP_DIRS": True,
                        "DIRS": [],
                        "OPTIONS": {"context_processors": []},
                    }
                ],
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()
            from django.contrib import admin
            from django.contrib.auth.models import Permission, User
            from django.contrib.contenttypes.models import ContentType
            from django.db import connection
            from django.test import Client

            urlpatterns = [path("admin/", admin.site.urls)]

            call_command("migrate", verbosity=0, interactive=False)

            shared = apps.get_model("shared_app", "Location")
            host = apps.get_model("host_app", "Location")
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(shared)
            obj = shared.objects.create(name="tokyo")

            changelist_url = reverse("admin:host_app_location_changelist")
            change_url = reverse("admin:host_app_location_change", args=[obj.pk])
            assert changelist_url == "/admin/host_app/location/"
            assert change_url == f"/admin/host_app/location/{obj.pk}/change/"

            host_ct = ContentType.objects.get(app_label="host_app", model="location")
            shared_ct = ContentType.objects.get(app_label="shared_app", model="location")
            assert host_ct != shared_ct

            host_perm_codes = set(
                Permission.objects.filter(content_type=host_ct).values_list("codename", flat=True)
            )
            shared_perm_codes = set(
                Permission.objects.filter(content_type=shared_ct).values_list("codename", flat=True)
            )
            expected = {"add_location", "change_location", "delete_location", "view_location"}
            assert expected.issubset(host_perm_codes)
            assert expected.issubset(shared_perm_codes)

            user = User.objects.create_superuser("admin", "admin@example.com", "pass")
            client = Client()
            assert client.login(username="admin", password="pass")
            response = client.get(change_url)
            assert response.status_code == 200
            assert b'name="name"' in response.content
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_proxy_wrapper_state_only_step_with_separate_database_and_state(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            from django.db import connection
            import django

            settings.configure(
                INSTALLED_APPS=["shared_app", "host_app"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()

            from django.db.migrations.operations.models import CreateModel
            from django.db.migrations.operations.special import SeparateDatabaseAndState
            from django.db.migrations.state import ProjectState

            shared = apps.get_model("shared_app", "Location")
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(shared)

            before_tables = set(connection.introspection.table_names())

            from_state = ProjectState.from_apps(apps)
            to_state = from_state.clone()
            op = SeparateDatabaseAndState(
                database_operations=[],
                state_operations=[
                    CreateModel(
                        name="Location",
                        fields=[],
                        options={"proxy": True},
                        bases=("shared_app.location",),
                        managers=[],
                    )
                ],
            )
            op.state_forwards("host_app", to_state)
            with connection.schema_editor() as schema_editor:
                op.database_forwards("host_app", schema_editor, from_state, to_state)

            after_tables = set(connection.introspection.table_names())
            assert before_tables == after_tables

            state_host = to_state.apps.get_model("host_app", "Location")
            state_shared = to_state.apps.get_model("shared_app", "Location")
            assert state_host._meta.proxy is True
            assert state_host._meta.concrete_model is state_shared
            assert state_host._meta.db_table == "piano_map_location"
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_separate_database_and_state_can_swap_host_concrete_to_proxy_without_table_changes(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
        }
        script = """
            from django.conf import settings
            from django.db import connection, models
            import django

            settings.configure(
                INSTALLED_APPS=["shared_app", "host_app"],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()

            from django.db.migrations.operations.models import CreateModel, DeleteModel
            from django.db.migrations.operations.special import SeparateDatabaseAndState
            from django.db.migrations.state import ModelState, ProjectState

            # Simulate pre-migration state: host_app owns a concrete Location table.
            from_state = ProjectState()
            from_state.add_model(
                ModelState(
                    app_label="host_app",
                    name="Location",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("name", models.CharField(max_length=100)),
                    ],
                    options={"db_table": "piano_map_location"},
                    bases=(models.Model,),
                )
            )

            with connection.schema_editor() as schema_editor:
                create_host_table = CreateModel(
                    name="Location",
                    fields=[
                        ("id", models.AutoField(primary_key=True)),
                        ("name", models.CharField(max_length=100)),
                    ],
                    options={"db_table": "piano_map_location"},
                )
                create_host_table.database_forwards("host_app", schema_editor, ProjectState(), from_state)
            before_tables = set(connection.introspection.table_names())

            # 1) Add shared_app concrete model as state-only (table already exists).
            to_state = from_state.clone()
            add_shared_state = SeparateDatabaseAndState(
                database_operations=[],
                state_operations=[
                    CreateModel(
                        name="Location",
                        fields=[
                            ("id", models.AutoField(primary_key=True)),
                            ("name", models.CharField(max_length=100)),
                        ],
                        options={"db_table": "piano_map_location"},
                    )
                ],
            )
            add_shared_state.state_forwards("shared_app", to_state)
            with connection.schema_editor() as schema_editor:
                add_shared_state.database_forwards("shared_app", schema_editor, from_state, to_state)

            # 2) Replace host_app concrete model state with proxy model state only.
            final_state = to_state.clone()
            swap_host_to_proxy = SeparateDatabaseAndState(
                database_operations=[],
                state_operations=[
                    DeleteModel(name="Location"),
                    CreateModel(
                        name="Location",
                        fields=[],
                        options={"proxy": True},
                        bases=("shared_app.location",),
                        managers=[],
                    ),
                ],
            )
            swap_host_to_proxy.state_forwards("host_app", final_state)
            with connection.schema_editor() as schema_editor:
                swap_host_to_proxy.database_forwards("host_app", schema_editor, to_state, final_state)

            after_tables = set(connection.introspection.table_names())
            assert before_tables == after_tables

            state_host = final_state.apps.get_model("host_app", "Location")
            state_shared = final_state.apps.get_model("shared_app", "Location")
            assert state_host._meta.proxy is True
            assert state_host._meta.concrete_model is state_shared
            assert state_host._meta.db_table == "piano_map_location"
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_proxy_admin_uses_proxy_permissions_for_non_superuser_access(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
            "host_app/admin.py": """
                from django.contrib import admin
                from .models import Location


                @admin.register(Location)
                class LocationAdmin(admin.ModelAdmin):
                    pass
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            from django.core.management import call_command
            from django.urls import path, reverse
            import django

            settings.configure(
                INSTALLED_APPS=[
                    "django.contrib.admin",
                    "django.contrib.auth",
                    "django.contrib.contenttypes",
                    "django.contrib.sessions",
                    "shared_app",
                    "host_app",
                ],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                ROOT_URLCONF=__name__,
                MIDDLEWARE=[
                    "django.contrib.sessions.middleware.SessionMiddleware",
                    "django.contrib.auth.middleware.AuthenticationMiddleware",
                ],
                TEMPLATES=[
                    {
                        "BACKEND": "django.template.backends.django.DjangoTemplates",
                        "APP_DIRS": True,
                        "DIRS": [],
                        "OPTIONS": {"context_processors": []},
                    }
                ],
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()
            from django.contrib import admin
            from django.contrib.auth.models import Permission, User
            from django.db import connection
            from django.test import Client

            urlpatterns = [path("admin/", admin.site.urls)]

            call_command("migrate", verbosity=0, interactive=False)
            shared = apps.get_model("shared_app", "Location")
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(shared)
            obj = shared.objects.create(name="tokyo")
            change_url = reverse("admin:host_app_location_change", args=[obj.pk])

            user = User.objects.create_user("staff", "staff@example.com", "pass", is_staff=True)
            host_change = Permission.objects.get(codename="change_location", content_type__app_label="host_app")
            shared_change = Permission.objects.get(codename="change_location", content_type__app_label="shared_app")

            user.user_permissions.add(shared_change)
            assert user.has_perm("shared_app.change_location") is True
            assert user.has_perm("host_app.change_location") is False
            client = Client()
            assert client.login(username="staff", password="pass")
            denied = client.get(change_url)
            assert denied.status_code == 403

            user.user_permissions.add(host_change)
            user = User.objects.get(pk=user.pk)
            assert user.has_perm("host_app.change_location") is True
            client = Client()
            assert client.login(username="staff", password="pass")
            allowed = client.get(change_url)
            assert allowed.status_code == 200
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_permission_sync_from_concrete_to_proxy_restores_staff_admin_access(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
            "host_app/admin.py": """
                from django.contrib import admin
                from .models import Location


                @admin.register(Location)
                class LocationAdmin(admin.ModelAdmin):
                    pass
            """,
        }
        script = """
            from django.apps import apps
            from django.conf import settings
            from django.core.management import call_command
            from django.urls import path, reverse
            import django

            settings.configure(
                INSTALLED_APPS=[
                    "django.contrib.admin",
                    "django.contrib.auth",
                    "django.contrib.contenttypes",
                    "django.contrib.sessions",
                    "shared_app",
                    "host_app",
                ],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                ROOT_URLCONF=__name__,
                MIDDLEWARE=[
                    "django.contrib.sessions.middleware.SessionMiddleware",
                    "django.contrib.auth.middleware.AuthenticationMiddleware",
                ],
                TEMPLATES=[
                    {
                        "BACKEND": "django.template.backends.django.DjangoTemplates",
                        "APP_DIRS": True,
                        "DIRS": [],
                        "OPTIONS": {"context_processors": []},
                    }
                ],
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()
            from django.contrib import admin
            from django.contrib.auth.models import Group, Permission, User
            from django.db import connection
            from django.test import Client

            urlpatterns = [path("admin/", admin.site.urls)]

            call_command("migrate", verbosity=0, interactive=False)
            shared = apps.get_model("shared_app", "Location")
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(shared)
            obj = shared.objects.create(name="tokyo")
            change_url = reverse("admin:host_app_location_change", args=[obj.pk])

            group = Group.objects.create(name="editors")
            shared_change = Permission.objects.get(codename="change_location", content_type__app_label="shared_app")
            group.permissions.add(shared_change)
            user = User.objects.create_user("staff", "staff@example.com", "pass", is_staff=True)
            user.groups.add(group)

            client = Client()
            assert client.login(username="staff", password="pass")
            denied = client.get(change_url)
            assert denied.status_code == 403

            # Sync rule: copy shared_app.* permissions to matching host_app.* permissions by codename.
            for shared_perm in Permission.objects.filter(content_type__app_label="shared_app"):
                try:
                    host_perm = Permission.objects.get(
                        content_type__app_label="host_app",
                        content_type__model=shared_perm.content_type.model,
                        codename=shared_perm.codename,
                    )
                except Permission.DoesNotExist:
                    continue
                group.permissions.add(host_perm)

            user = User.objects.get(pk=user.pk)
            assert user.has_perm("host_app.change_location") is True
            client = Client()
            assert client.login(username="staff", password="pass")
            allowed = client.get(change_url)
            assert allowed.status_code == 200
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_permission_sync_is_idempotent_and_skips_missing_proxy_permissions(self):
        files = {
            "shared_app/__init__.py": "",
            "shared_app/apps.py": """
                from django.apps import AppConfig


                class SharedAppConfig(AppConfig):
                    name = "shared_app"
            """,
            "shared_app/models.py": """
                from django.db import models


                class Location(models.Model):
                    name = models.CharField(max_length=100)

                    class Meta:
                        db_table = "piano_map_location"
            """,
            "host_app/__init__.py": "",
            "host_app/apps.py": """
                from django.apps import AppConfig


                class HostAppConfig(AppConfig):
                    name = "host_app"
            """,
            "host_app/models.py": """
                from shared_app.models import Location as SharedLocation


                class Location(SharedLocation):
                    class Meta:
                        proxy = True
            """,
        }
        script = """
            from django.conf import settings
            from django.core.management import call_command
            import django

            settings.configure(
                INSTALLED_APPS=[
                    "django.contrib.auth",
                    "django.contrib.contenttypes",
                    "shared_app",
                    "host_app",
                ],
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
                SECRET_KEY="test",
                DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            )
            django.setup()

            from django.contrib.auth.models import Group, Permission

            call_command("migrate", verbosity=0, interactive=False)

            group = Group.objects.create(name="editors")
            shared_perms = Permission.objects.filter(content_type__app_label="shared_app")
            group.permissions.add(*shared_perms)

            # Add an unmatched source permission to ensure missing host side is skipped.
            orphan = Permission.objects.create(
                name="Can use orphan feature",
                content_type=shared_perms.first().content_type,
                codename="orphan_feature",
            )
            group.permissions.add(orphan)

            def sync_permissions():
                added = 0
                for shared_perm in Permission.objects.filter(content_type__app_label="shared_app"):
                    host_perm = Permission.objects.filter(
                        content_type__app_label="host_app",
                        content_type__model=shared_perm.content_type.model,
                        codename=shared_perm.codename,
                    ).first()
                    if not host_perm:
                        continue
                    if not group.permissions.filter(pk=host_perm.pk).exists():
                        group.permissions.add(host_perm)
                        added += 1
                return added

            added_first = sync_permissions()
            added_second = sync_permissions()

            host_perm_count = group.permissions.filter(content_type__app_label="host_app").count()
            assert host_perm_count == 4  # add/change/delete/view for Location
            assert added_first == 4
            assert added_second == 0
            assert group.permissions.filter(codename="orphan_feature").exists()
        """

        result = self._run_django_poc(files, script)

        self.assertEqual(result.returncode, 0, result.stderr)
