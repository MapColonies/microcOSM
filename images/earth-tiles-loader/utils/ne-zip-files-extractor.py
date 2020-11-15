# this script creates the correct yaml for the external data file sources part
# it needs a flat directory structure in the zip like in natural earth

import zipfile
import requests
import yaml
import io
import zipfile

urls = ('https://naciscdn.org/naturalearth/110m/cultural/ne_110m_populated_places.zip',
        'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_populated_places.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_label_points.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_label_points.zip',
        'https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.zip',
        'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_boundary_lines_land.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_boundary_lines_land.zip',
        'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_boundary_lines_disputed_areas.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_boundary_lines_disputed_areas.zip',
        'https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip',
        'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip',
        'https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_1_states_provinces_lines.zip',
        'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_1_states_provinces_lines.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces_lines.zip',
        'https://naciscdn.org/naturalearth/110m/physical/ne_110m_land.zip',
        'https://naciscdn.org/naturalearth/50m/physical/ne_50m_land.zip',
        'https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip',
        'https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_1_states_provinces_lakes.zip',
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_roads.zip')

output = {}


def create_data_entry(url):
    download = requests.get(url)
    filename = url.split('/')[-1].split('.')[0]
    zip = zipfile.ZipFile(io.BytesIO(download.content))
    file_list = map(lambda x: x.filename, zip.filelist)
    filtered_file_list = filter(
        lambda x: 'README' not in x and 'VERSION' not in x, file_list)
    output[filename] = {'url': url, 'type': 'shp', 'archive': {
        'format': 'zip', 'files': list(filtered_file_list)}, 'file': '{}.shp'.format(filename)}


for url in urls:
    create_data_entry(url)

with open('data.yml', 'w') as outfile:
    yaml.dump(output, outfile, default_flow_style=False)
