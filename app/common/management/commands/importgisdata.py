import os
import tempfile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Import GIS data for address matching"
    requires_system_checks = False

    def handle(self, *args, **options):
        td = tempfile.TemporaryDirectory()
        cursor = connection.cursor()

        psql = f"PGPASSWORD={settings.DATABASES['default']['PASSWORD']} PGHOST={settings.DATABASES['default']['HOST']} PGUSER={settings.DATABASES['default']['USER']} PGDATABASE={settings.DATABASES['default']['NAME']} psql"

        # WI
        r = os.system(
            f"cd {td.name} && wget https://opendata.arcgis.com/datasets/47009ab057d8401eb9025c4fc024a12a_0.zip && unzip 47009ab057d8401eb9025c4fc024a12a_0.zip"
        )
        assert r == 0
        try:
            cursor.execute("drop table official_region_geom_wi")
        except:
            pass
        os.system(
            f"cd {td.name} && shp2pgsql -s 4326 CTV_Jan_2020.shp official_region_geom_wi | {psql}"
        )

        # MA
        r = os.system(
            f"cd {td.name} && wget http://download.massgis.digital.mass.gov/shapefiles/state/wardsprecincts_poly.zip && unzip wardsprecincts_poly.zip"
        )
        assert r == 0
        try:
            cursor.execute("drop table official_region_geom_ma")
        except:
            pass
        r = os.system(
            f"cd {td.name} && shp2pgsql -s 26986:4326 WARDSPRECINCTS_POLY.shp official_region_geom_ma | {psql}"
        )
        assert r == 0
