from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "LocalHub Core"

    def ready(self):
        import core.signals  # noqa: F401  (registers the post_save receiver)
