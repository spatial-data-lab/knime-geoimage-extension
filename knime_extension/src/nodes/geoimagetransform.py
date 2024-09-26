import knime_extension as knext
import util.knime_utils as knut

__category = knext.category(
    path="/community/geoimage",
    level_id="geoimagetransform",
    name="GeoImage Transform",
    description="Nodes that process spatial image data in various ways.",
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
    name="GeoImage to Table",
    node_type=knext.NodeType.MANIPULATOR,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "GeoImagetoTable.png"  # Uses the global icon path definition
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
        im_data, _, _= pickle.loads(imagedata) # Unpack the image data and profile

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
    icon_path=__NODE_ICON_PATH + "RasterPointValues.png"  # Uses the global icon path definition
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
        img, profile, _ = pickle.loads(imagedata) # Unpack the image data and profile
       
        
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
    

############################################
# Table to Referenced GeoImage
############################################

@knext.node(
    name="Table to Referenced GeoImage",
    node_type=knext.NodeType.MANIPULATOR,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "TableToGeoImage.png"  # Uses the global icon path definition
)

@knext.input_binary(
    name="Input Raster Reference",
    description="Input raster image reference including profile and bounds.",
    id="rasterio.data.profile",
)
@knext.input_table(
    name="Raster Data Table",
    description="Table containing raster data values for constructing the new geo-referenced image.",
)

@knext.output_binary(
    name="Output GeoImage",
    description="Geo-referenced raster image generated from the input table using the original raster reference.",
    id="rasterio.data.profile",
)

class TableToGeoImageNode:
    value_columns = knext.MultiColumnParameter(
        "Value Columns",
        """Select one or more columns containing the raster values for the new geo-referenced image. 
        Each selected column will be used as a separate band in the output image.""",
        column_filter=knut.is_numeric,  
        port_index=1, 
    )

    def configure(self, configure_context, input_binary_schema,input_schema):
        return None
    
    def execute(self, exec_context, imagedata,input_table):

        exec_context.set_progress(0.1, "Profile and metadata extracted...")
        import pickle
        img, profile, bounds = pickle.loads(imagedata) # Unpack the image data and profile
        img_df = input_table.to_pandas()
 
        bands = []
        for col in self.value_columns:
            img_df[col] = img_df[col].astype(int)
            band_img = img_df[col].values.reshape((img.shape[1], img.shape[2]))  
            bands.append(band_img)

        import numpy as np
        new_raster = np.stack(bands, axis=0)  

        # update profile
        new_profile = profile.copy()
        new_profile.update({
            'count': len(bands),  # update bands
        })

      
        exec_context.set_progress(0.8, "Profile and metadata extracted...")
        
        import pickle
        imagedata = pickle.dumps([new_raster, profile,bounds])

        return imagedata


############################################
# Clip Raster by Polygon
############################################

@knext.node(
    name="Clip Raster by Polygon",
    node_type=knext.NodeType.MANIPULATOR,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "RasterClip.png"  # Uses the global icon path definition
)

@knext.input_binary(
    name="Input Raster Reference",
    description="Raster image to be clipped by the input table's geometry.",
    id="rasterio.data.profile",
)
@knext.input_table(
    name="Raster Data Table",
    description="Table containing polygon geometry for clipping the raster.",
)

@knext.output_binary(
    name="Clipped Raster",
    description="Output raster image clipped to the geometry from the input table.",
    id="rasterio.data.profile",
)

class RasterClipNode:
    geo_col = knext.ColumnParameter(
        "Geometry Column", 
        "Select the geometry column",
        port_index=1, 
        column_filter=knut.is_geo
    )

    crop = knext.BoolParameter(
        "Crop Raster",
        """If checked, the raster will be cropped to the geometry's extent. 
        If unchecked, only pixels outside the geometry will be masked, 
        but the raster shape will remain unchanged.""",
        default_value=True   
    )  

    def configure(self, configure_context, input_binary_schema,input_schema):
        self.geo_col = knut.column_exists_or_preset(configure_context, self.geo_col, input_schema, knut.is_geo)
        return None
    
    def execute(self, exec_context, imagedata,input_table):

        exec_context.set_progress(0.1, "Profile and metadata extracted...")

        import pickle
        im_data, profile, bounds = pickle.loads(imagedata) # Unpack the image data and profile
 

        import geopandas as gp
        gdf = gp.GeoDataFrame(input_table.to_pandas(), geometry=self.geo_col)
        gdf = gdf.to_crs(profile['crs'])

        import rasterio
        from rasterio.mask import mask

        with rasterio.MemoryFile() as memfile:
            with memfile.open(**profile) as dataset:
                dataset.write(im_data)
                clipped_tiff, tiff_transform = mask(dataset, gdf.geometry, crop=self.crop)
                clipped_profile = dataset.profile.copy()
                clipped_profile.update({
                    "height": clipped_tiff.shape[1],
                    "width": clipped_tiff.shape[2],
                    "transform": tiff_transform
                })


        exec_context.set_progress(0.9, "Serialization of output data...")

        output_data = pickle.dumps([clipped_tiff, clipped_profile, bounds])
        return output_data
