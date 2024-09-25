import knime_extension as knext
import util.knime_utils as knut

__category = knext.category(
    path="/community/geoimage",
    level_id="geoimagetransform",
    name="Image Transform",
    description="Nodes that read and write spatial image data in various formats.",
    # starting at the root folder of the extension_module parameter in the knime.yml file
    icon="icons/icon/TransformCategory.png",
    after="geoimageio",
)

# Root path for all node icons in this file
__NODE_ICON_PATH = "icons/icon/Transform/"


############################################
# GeoImage to Table
############################################

@knext.node(
    name="Image to Table",
    node_type=knext.NodeType.MANIPULATOR,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "GeoFileManipulate.png"  # Uses the global icon path definition
)
@knext.input_binary(
    name="Image object",
    description="Serialized image data and profile from a GeoTIFF file.",
    id="rasterio.data.profile"
)
@knext.output_table(
    name="Image DataFrame",
    description="Reshaped image data as a table with pixel values and coordinates (row, col)."
)
class ImageToTableNode:
    def configure(self, configure_context, input_binary_schema):
        # No special configuration required for this node
        return None

    def execute(self, exec_context: knext.ExecutionContext, imagedata):
        exec_context.set_progress(0.1, "Starting image reshaping...")

        # Deserialize the input binary data to retrieve image data and profile
        import pickle
        im_data, _ = pickle.loads(imagedata) # Unpack the image data and profile

        # Reshape image from (Bands, Height, Width) to (Height * Width, Bands)
        img_reshaped = im_data.transpose(1, 2, 0).reshape(-1, im_data.shape[0])

        import pandas as pd
        import numpy as np
        # Convert reshaped image data to a pandas DataFrame with band values as columns
        img_df = pd.DataFrame(
            img_reshaped.astype(np.float32), 
            columns=[f"Band_{i+1}" for i in range(im_data.shape[0])]
        )

        # Generate row and column indices for the image and add them to the DataFrame
        rows, cols = np.indices(im_data.shape[1:])
        img_df['row'] = rows.flatten()
        img_df['col'] = cols.flatten()

        exec_context.set_progress(0.9, "Data reshaped successfully.")
        return knext.Table.from_pandas(img_df)  

############################################
# Extract Values to Points
############################################

@knext.node(
    name="Extract Values to Points",
    node_type=knext.NodeType.MANIPULATOR,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "GeoFileManipulate.png"  # Uses the global icon path definition
)

@knext.input_table(
    name="Input Table", 
    description="Table containing geometry column with point geometries."
)

@knext.input_binary(
    name="Image object",
    description="Serialized image data and profile from a GeoTIFF file.",
    id="rasterio.data.profile"
)

@knext.output_table(
    name="Output Table", 
    description="Table with extracted raster values added to point geometries."
)

class ExtractValuesToPoints:
    geo_col = knext.ColumnParameter(
        "Geometry Column", 
        "Select the geometry column",
        port_index=0, 
        column_filter=knut.is_geo_point
        )

    def configure(self, configure_context, input_schema, input_binary_schema):
        self.geo_col = knut.column_exists_or_preset(
            configure_context,self.geo_col,input_schema, 
            knut.is_geo_point)       
        return None

    def execute(self, exec_context, input_table,imagedata):
        exec_context.set_progress(0.1, "Starting image reshaping...")

        # Deserialize the input binary data to retrieve image data and profile
        import pickle
        img, profile = pickle.loads(imagedata) # Unpack the image data and profile
       
        
        import geopandas as gp
        import numpy as np
        import pandas as pd
        from rasterio.transform import rowcol
        gdf = gp.GeoDataFrame(input_table.to_pandas(), geometry=self.geo_col)
        gdf_r = gdf.to_crs(profile['crs'])
        points = gdf_r.geometry.apply(lambda geom: (geom.x, geom.y))

        sample_coords = [rowcol(profile['transform'], x, y) for x, y in points]
        
        num_bands = img.shape[0]  
        sample_values = np.array([img[:, row, col] for row, col in sample_coords])

        exec_context.set_progress(0.9, "Data extracted successfully.")

        band_columns = [f"Band_{i+1}" for i in range(num_bands)]  
        data = pd.DataFrame(sample_values.astype(np.float32), columns=band_columns)
        
        original_gdf = gdf.reset_index(drop=True)
        data = pd.concat([original_gdf, data], axis=1)
        
        return knext.Table.from_pandas(data )  

