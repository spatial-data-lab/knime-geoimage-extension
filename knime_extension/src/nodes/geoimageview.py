import knime_extension as knext
import util.knime_utils as knut

__category = knext.category(
    path="/community/geoimage",
    level_id="geoimageview",
    name="GeoImage View",
    description="Nodes that visualize spatial image data in various formats.",
    # starting at the root folder of the extension_module parameter in the knime.yml file
    icon="icons/icon/ViewCategory.png",
    after="geoimagetransform",
)

# Root path for all node icons in this file
__NODE_ICON_PATH = "icons/icon/Visualization/"


############################################
# GeoImage View
############################################

@knext.node(
    name="GeoImage View",
    node_type=knext.NodeType.VISUALIZER,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "GeoImageView.png"  # Uses the global icon path definition
)


@knext.input_binary(
    name="Input Raster",
    description="Input raster image data to visualize on the Folium map.",
    id="rasterio.data.profile",
)

@knext.output_view(
    name="Raster Folium View",
    description="Interactive map displaying the raster image with customizable color settings",
)

class GeoImageViewNode:
    band_selection = knext.StringParameter(
        "Band(s) for visualization",
        """Select one or 3 bands for visualization (e.g., "1" for grayscale, "2,3,4" for RGB). 
        Band indices start from 1.""",
        default_value="1",
    )
    
    
    color_map = knext.StringParameter(
        "Color map",
        "Select the color map for visualization.",
        default_value="viridis",
        enum=[ 
            "viridis", "plasma", "inferno", "magma", "cividis", "Greys", "Purples", 
            "Blues", "Greens", "Oranges", "Reds", "YlOrBr", "YlGnBu", "cool", "hot", "spring"
        ]
    )

    opacity = knext.DoubleParameter(
        "Opacity",
        """Set the opacity of the image overlay on the map. 
        The value should be between 0 (completely transparent) and 1 (completely opaque).""",
        default_value=0.7,
        min_value=0.0,
        max_value=1.0
    )

    base_map = knext.StringParameter(
            "Base map",
            """Select the base map to use for the visualization. If choose 'Don't show base map', the base map will be hidden.
            The default base map is 'OpenStreetMap'.
            See [Folium base maps](https://python-visualization.github.io/folium/quickstart.html#Tiles).""",
            default_value="OpenStreetMap",
            enum=[
                "CartoDB DarkMatter",
                "CartoDB DarkMatterNoLabels",
                "CartoDB DarkMatterOnlyLabels",
                "CartoDB Positron",
                "CartoDB PositronNoLabels",
                "CartoDB PositronOnlyLabels",
                "CartoDB Voyager",
                "CartoDB VoyagerLabelsUnder",
                "CartoDB VoyagerNoLabels",
                "CartoDB VoyagerOnlyLabels",
                "Esri DeLorme",
                "Esri NatGeoWorldMap",
                "Esri OceanBasemap",
                "Esri WorldGrayCanvas",
                "Esri WorldImagery",
                "Esri WorldPhysical",
                "Esri WorldShadedRelief",
                "Esri WorldStreetMap",
                "Esri WorldTerrain",
                "Esri WorldTopoMap",
                "Gaode Normal",
                "Gaode Satellite",
                "NASAGIBS ASTER_GDEM_Greyscale_Shaded_Relief",
                "NASAGIBS BlueMarble",
                "NASAGIBS BlueMarble3031",
                "NASAGIBS BlueMarble3413",
                "NASAGIBS ModisAquaBands721CR",
                "NASAGIBS ModisAquaTrueColorCR",
                "NASAGIBS ModisTerraAOD",
                "NASAGIBS ModisTerraBands367CR",
                "NASAGIBS ModisTerraBands721CR",
                "NASAGIBS ModisTerraChlorophyll",
                "NASAGIBS ModisTerraLSTDay",
                "NASAGIBS ModisTerraSnowCover",
                "NASAGIBS ModisTerraTrueColorCR",
                "NASAGIBS ViirsEarthAtNight2012",
                "NASAGIBS ViirsTrueColorCR",
                "OpenRailwayMap",
                "OpenStreetMap",
                "Stamen Terrain",
                "Stamen TerrainBackground",
                "Stamen TerrainLabels",
                "Stamen Toner",
                "Stamen TonerBackground",
                "Stamen TonerHybrid",
                "Stamen TonerLabels",
                "Stamen TonerLines",
                "Stamen TonerLite",
                "Stamen TopOSMFeatures",
                "Stamen TopOSMRelief",
                "Stamen Watercolor",
                "Strava All",
                "Strava Ride",
                "Strava Run",
                "Strava Water",
                "Strava Winter",
            ],
    )
    
    def configure(self, configure_context, input_binary_schema):
        # No special configuration required for this node
        return None
    
    def execute(self, exec_context, imagedata):
        exec_context.set_progress(0.1, "Processing raster data...")

        # get imagedata
        import pickle
        img, profile, bounds = pickle.loads(imagedata)

        # get band
        bands = [int(band) - 1 for band in self.band_selection.split(',')]

        # EPSG to EPSG:4326
        from rasterio.warp import transform_bounds
        import folium
        import matplotlib.pyplot as plt
        import numpy as np
        left, bottom, right, top = bounds
        bounds = transform_bounds(profile['crs'], 'EPSG:4326', left, bottom, right, top)

        if len(bands) == 1:
            # single band
            band = img[bands[0]]
            band_norm = (band - np.nanmin(band)) / (np.nanmax(band) - np.nanmin(band))

            # olium 
            m = folium.Map(location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
                           tiles=self.base_map)
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # map
            cmap = plt.get_cmap(self.color_map)

            # overlay
            image_overlay = folium.raster_layers.ImageOverlay(
                band_norm,
                bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                opacity=self.opacity,
                colormap=lambda x: cmap(x),
            )
            image_overlay.add_to(m)

        elif len(bands) == 3:
            # (RGB)
            r = img[bands[0]]
            g = img[bands[1]]
            b = img[bands[2]]

            # Normalization
            r_norm = (r - np.nanmin(r)) / (np.nanmax(r) - np.nanmin(r))
            g_norm = (g - np.nanmin(g)) / (np.nanmax(g) - np.nanmin(g))
            b_norm = (b - np.nanmin(b)) / (np.nanmax(b) - np.nanmin(b))

            # Stack
            rgb_image = np.dstack((r_norm, g_norm, b_norm))

            # Folium 
            m = folium.Map(location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2],
                           tiles=self.base_map)
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # overlay
            image_overlay = folium.raster_layers.ImageOverlay(
                rgb_image,
                bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                opacity=self.opacity
            )
            image_overlay.add_to(m)

        else:
            raise ValueError("Only 1-band or 3-band visualizations are supported.")

        # All map control
        folium.LayerControl().add_to(m)

        # HTML for KNIME view
        html = m.get_root().render()
        return knext.view(html)       
    

############################################
# GeoImage View Static
############################################

@knext.node(
    name="GeoImage View Static",
    node_type=knext.NodeType.VISUALIZER,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "GeoImageViewStatic.png"  # Uses the global icon path definition
)

@knext.input_binary(
    name="Input Raster",
    description="Input geo-image data for visualization.",
    id="rasterio.data.profile",
)

@knext.output_view(
    name="Static Image View",
    description="Displays a static image view of the input geo-image.",
)

class GeoImageViewStaticNode:
    band_selection = knext.StringParameter(
        "Band(s) for visualization",
        """Select one or 3 bands for visualization (e.g., "1" for grayscale, "2,3,4" for RGB). 
        Band indices start from 1.""",
        default_value="1",
    )
        
    color_map = knext.StringParameter(
        "Color map",
        "Select the color map for visualization.",
        default_value="viridis",
        enum=[ 
            "viridis", "plasma", "inferno", "magma", "cividis", "Greys", "Purples", 
            "Blues", "Greens", "Oranges", "Reds", "YlOrBr", "YlGnBu", "cool", "hot", "spring"
        ]
    )

    vmin = knext.DoubleParameter(
        "Min Value",
        "Set the minimum value for the color scale.",
        default_value=0.1,
    )
    
    vmax = knext.DoubleParameter(
        "Max Value",
        "Set the maximum value for the color scale.",
        default_value=1,
    )

    def configure(self, configure_context, input_binary_schema):
            # No special configuration required for this node
        return None

    def execute(self, exec_context, imagedata):
        exec_context.set_progress(0.1, "Loading raster data and metadata...")

        import pickle
        import matplotlib.pyplot as plt
        from io import BytesIO
        import re
        import numpy as np

        # Deserialize raster data
        im_data, profile, bounds = pickle.loads(imagedata)

        # Parse the band selection (either single band or RGB bands)
        bands = list(map(int, re.split(r'\s*,\s*', self.band_selection)))

        if len(bands) == 1:
            # Single-band grayscale visualization
            raster_data = im_data[bands[0] - 1]  # Band indices start from 1, but im_data uses 0-based indexing

            exec_context.set_progress(0.3, "Creating grayscale plot...")

            fig, ax = plt.subplots()

            # Display the single band with a color map
            im = ax.imshow(raster_data, cmap=self.color_map, vmin=self.vmin, vmax=self.vmax)

            # Add colorbar
            cbar = fig.colorbar(im, ax=ax, orientation='horizontal', shrink=0.99)
            cbar.set_label('Value')

        elif len(bands) == 3:
            # RGB visualization
            exec_context.set_progress(0.3, "Creating RGB plot...")

            # Stack selected bands into an RGB array (shape: [height, width, 3])
            raster_data = np.stack([im_data[b - 1] for b in bands], axis=-1)

            fig, ax = plt.subplots()

            # Display RGB image
            ax.imshow(raster_data)

        else:
            raise ValueError("Please select either 1 or 3 bands for visualization.")

        # Set image title
        ax.set_title("Static GeoImage View", fontsize=14)

        # Optionally turn off the axis
        ax.set_axis_off()

        fig.set_size_inches(8, 6)

        exec_context.set_progress(0.6, "Exporting plot...")

        # Create in-memory image buffer
        # out_image_buffer = BytesIO()

        # # Save figure to buffer in the selected image format (SVG/PNG)
        # fig.savefig(out_image_buffer, format=self.image_type.lower(), bbox_inches='tight', pad_inches=0.1)

        exec_context.set_progress(0.9, "Rendering view...")

        # Return image data and KNIME view
        return  knext.view_matplotlib(fig)
