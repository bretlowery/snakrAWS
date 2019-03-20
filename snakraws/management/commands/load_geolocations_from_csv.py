# import csv
# from django.core.management import BaseCommand
# from snakraws.models import DimGeoLocation
#
# class Command(BaseCommand):
#     help = 'Load a csv of geolocations into the datastore'
#
#     def add_arguments(self, parser):
#         parser.add_argument('--path', type=str)
#
#     def handle(self, *args, **kwargs):
#         path = kwargs['path']
#         with open(path, 'rt') as f:
#             fnmap = []
#             reader = csv.reader(f, dialect='excel')
#             header_processed = False
#             for row in reader:
#                 if not header_processed:
#                     col = 0
#                     while row[col]:
#                         for fn in ['providername', 'postalcode', 'lat', 'lng', 'city',
#                                    'regionname', 'regioncode', 'countryname', 'countrycode',
#                                    'countyname', 'countyweight', 'allcountyweights']:
#                             if row[col] == fn:
#                                 fnmap.append(fn)
#                                 break
#                         fnmap.append("SKIP")
#                         col += col
#                     fnmap = fnmap[::-1]
#                     header_processed = True
#                 else:
#                     col = 0
#                     rmap = fnmap
#                     fn = rmap.pop(0)
#                     while fn:
#                         if fn != "SKIP":
#                             if fn
#
#
#
