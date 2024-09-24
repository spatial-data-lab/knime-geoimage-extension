import knime_extension as knext
import util.knime_utils as knut

__category = knext.category(
    path="/community/geoimage",
    level_id="geoimageio",
    name="Image IO",
    description="Nodes that read and write spatial image data in various formats.",
    # starting at the root folder of the extension_module parameter in the knime.yml file
    icon="icons/icon/IOCategory.png",
)

# Root path for all node icons in this file
__NODE_ICON_PATH = "icons/icon/IO/"


############################################
# GeoFile Reader
############################################
@knext.node(
    name="GeoTiff Reader",
    node_type=knext.NodeType.SOURCE,
    icon_path=__NODE_ICON_PATH + "GeoFileReader.png",
    category=__category,
    after="",
)

@knut.rasterio_node_description(
    short_description="Reads a GeoTIFF file and outputs the image data, profile, and metadata.",
    description="This node reads a GeoTIFF image file, outputs the image data, metadata profile as a table, and a serialized image object.",
    references={
        "Rasterio Documentation": "https://rasterio.readthedocs.io/",
        "GeoTIFF Format": "https://gdal.org/drivers/raster/geotiff.html"
    }
)
@knext.output_binary(
    name="Image object",
    description="Serialized image data and profile from the GeoTIFF file.",
    id="rasterio.data.profile",
)
@knext.output_table(
    name="Profile table",
    description="Table of the image profile metadata, including bounds and shape."
)
class GeoTiffReaderNode:
    data_url = knext.StringParameter(
        "Input file path",
        "The file path for reading the GeoTIFF image.",
        "",
    )

    def configure(self, configure_context):
        # TODO Create combined schema
        return None

    def execute(self, exec_context: knext.ExecutionContext):
        exec_context.set_progress(
            0.1, "Reading file (This might take a while without progress changes)"
        )
        import rasterio
        import pandas as pd
        dataset = rasterio.open(self.data_url)

        # Read numpy array and profile
        im_data = dataset.read()
        profile = dataset.profile
        bounds = [*dataset.bounds]  
        bounds_str = str(bounds)  

        # Profile to table
        flattened_profile = {k: str(v) for k, v in profile.items()}
        df_profile = pd.DataFrame(list(flattened_profile.items()), columns=['Property', 'Value'])
        
        # Add boundary and shape to Profile table
        additional_rows = pd.DataFrame([
            {'Property': 'bounds', 'Value': bounds_str},
            {'Property': 'shape', 'Value': str(im_data.shape)}
        ])
        df_profile = pd.concat([df_profile, additional_rows], ignore_index=True)
        exec_context.set_progress(0.8, "Profile and metadata extracted...")
        
        import pickle
        imagedata = pickle.dumps([im_data, profile])

        return imagedata, knext.Table.from_pandas(df_profile)


############################################
# GeoFile Reader
############################################
@knext.node(
    name="GeoTiff To Table",
    node_type=knext.NodeType.SOURCE,
    icon_path=__NODE_ICON_PATH + "GeoPackageReader.png",
    category=__category,
    after="",
)
@knext.input_binary(
    name="Image object",
    description="Pickle object from raterio package",
    id="rasterio.data.profile",
)
@knext.output_table(
    name="Output Table",
    description="Output table with image value",
)
class GeoTifftoTableNode:
    def configure(self, configure_context, input_binary_schema):
        # TODO Create combined schema
        return None

    def execute(self, exec_context: knext.ExecutionContext, image):
        exec_context.set_progress(
            0.4, "Reading file (This might take a while without progress changes)"
        )
        import rasterio
        import pickle
        import pandas as pd

        imagedata = pickle.loads(image)
        im_data = imagedata[0][0]
        # df = pd.DataFrame(im_data[0])
        df = pd.DataFrame(im_data)
        return knext.Table.from_pandas(df)
