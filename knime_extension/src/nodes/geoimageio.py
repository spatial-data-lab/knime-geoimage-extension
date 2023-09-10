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
@knext.output_binary(
    name="Image object",
    description="Pickle object from raterio package",
    id="rasterio.data.profile",
)
class GeoTiffReaderNode:
    data_url = knext.StringParameter(
        "Input file path",
        "The file path for reading data.",
        "",
    )

    def configure(self, configure_context):
        # TODO Create combined schema
        return None

    def execute(self, exec_context: knext.ExecutionContext):
        exec_context.set_progress(
            0.4, "Reading file (This might take a while without progress changes)"
        )
        import rasterio

        dataset = rasterio.open(self.data_url)
        im_data = dataset.read()
        profile = dataset.profile
        list_output = [im_data, profile]
        import pickle

        imagedata = pickle.dumps(list_output)

        return imagedata


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
