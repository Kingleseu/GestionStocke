from .models import SupplySiteSettings


def supply_site_settings(request):
    return {'supply_site_settings': SupplySiteSettings.get_solo()}
