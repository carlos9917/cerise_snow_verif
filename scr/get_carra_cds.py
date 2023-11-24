import cdsapi
import os
#URL = 'https://cds.climate.copernicus.eu/api/v2'
KEY = os.getenv("CDS_UID")
c = cdsapi.Client()
month="10"
year="2022"

c.retrieve(
    'reanalysis-carra-single-levels',
    {
        'format': 'grib',
        'domain': 'west_domain',
        'level_type': 'surface_or_atmosphere',
        'variable': 'fraction_of_snow_cover',
        'product_type': 'analysis',
        'time': [
            '00:00', '03:00', '06:00',
            '09:00', '12:00', '15:00',
            '18:00', '21:00',
        ],
        'year': year,
        'month': month,
        'day': [
            '01', '02', '03',
            '04', '05', '06',
            '07', '08', '09',
            '10', '11', '12',
            '13', '14', '15',
            '16', '17', '18',
            '19', '20', '21',
            '22', '23', '24',
            '25', '26', '27',
            '28', '29', '30',
            '31',
        ],
    },
    f'snow_fraction_{month}_{year}.grib')
