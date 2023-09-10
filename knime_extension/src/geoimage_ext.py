# The root category of all Geospatial categories
import knime_extension as knext
import sys

# This defines the root knime-geoimage-extension KNIME category that is displayed in the node repository
category = knext.category(
    path="/community",
    level_id="geoimage",  # this is the id of the category in the node repository #FIXME:
    name="knime-geoimage-extension",
    description="GeoImage Analytics for KNIME",
    # starting at the root folder of the extension_module parameter in the knime.yml file
    icon="icons/icon/Geolab/DvGlobalDOIlink.png",
)


import nodes.geoimageio
