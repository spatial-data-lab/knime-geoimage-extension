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
    node_type=knext.NodeType.MANIPULATOR,
    category=__category,  # Uses the global category definition
    icon_path=__NODE_ICON_PATH + "GeoImageView.png"  # Uses the global icon path definition
)

# 定义输入和输出端口
@knext.input_binary(
    name="Input Raster",
    description="Input raster image data to visualize on the Folium map.",
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

    def configure(self, configure_context, input_binary_schema):
        # No special configuration required for this node
        return None
    
    def execute(self, exec_context, imagedata):
        exec_context.set_progress(0.1, "Processing raster data...")

        # 反序列化输入栅格数据
        import pickle
        img, profile, bounds = pickle.loads(imagedata)

        # 获取波段选择，处理为列表形式
        bands = [int(band) - 1 for band in self.band_selection.split(',')]

        # 转换栅格的边界坐标为 EPSG:4326
        from rasterio.warp import transform_bounds
        import folium
        import matplotlib.pyplot as plt
        import numpy as np
        left, bottom, right, top = bounds
        bounds = transform_bounds(profile['crs'], 'EPSG:4326', left, bottom, right, top)

        if len(bands) == 1:
            # 单波段可视化
            band = img[bands[0]]
            band_norm = (band - np.nanmin(band)) / (np.nanmax(band) - np.nanmin(band))

            # 初始化 Folium 地图
            m = folium.Map(location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2])
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # 选择颜色映射
            cmap = plt.get_cmap(self.color_map)

            # 生成影像覆盖层
            image_overlay = folium.raster_layers.ImageOverlay(
                band_norm,
                bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                opacity=0.7,
                colormap=lambda x: cmap(x),
            )
            image_overlay.add_to(m)

        elif len(bands) == 3:
            # 多波段可视化 (RGB)
            r = img[bands[0]]
            g = img[bands[1]]
            b = img[bands[2]]

            # 归一化波段值
            r_norm = (r - np.nanmin(r)) / (np.nanmax(r) - np.nanmin(r))
            g_norm = (g - np.nanmin(g)) / (np.nanmax(g) - np.nanmin(g))
            b_norm = (b - np.nanmin(b)) / (np.nanmax(b) - np.nanmin(b))

            # 组合为 RGB 图像
            rgb_image = np.dstack((r_norm, g_norm, b_norm))

            # 初始化 Folium 地图
            m = folium.Map(location=[(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2])
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # 生成影像覆盖层
            image_overlay = folium.raster_layers.ImageOverlay(
                rgb_image,
                bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
                opacity=0.7
            )
            image_overlay.add_to(m)

        else:
            raise ValueError("Only 1-band or 3-band visualizations are supported.")

        # 添加图层控制
        folium.LayerControl().add_to(m)

        # 生成 HTML 代码用于 KNIME 视图
        html = m.get_root().render()
        return knext.view(html)       