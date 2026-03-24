import json
import os
import pickle
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, overload

import numpy as np
import pyproj
import shapely
from google.protobuf.json_format import MessageToDict
from pycityproto.city.map.v2 import map_pb2
from pydantic import BaseModel, Field
from shapely.geometry import Point, Polygon

from ..logger import get_logger
from ..s3 import S3Config, S3Client
from .utils.const import POI_CATG_DICT

__all__ = ["MapData", "MapConfig"]


class MapConfig(BaseModel):
    """Map configuration class."""

    file_path: str = Field(...)
    """Path to the map file. If s3 is enabled, the file will be downloaded from S3"""

    neighborhood_file_path: Optional[str] = Field(None)
    """Path to the neighborhood file."""


class MapData:
    """
    Map API
    """

    def __init__(self, config: MapConfig, s3config: S3Config):
        """
        Args:
        - config (MapConfig): Map config, Defaults to None.
        - s3config (S3Config): S3 configuration.
        """
        get_logger().info("MapData init")
        s3client = None
        if s3config.enabled:
            s3client = S3Client(s3config)
        map_data = None
        # 1. try to load from cache
        cache_suffix = ".cache"
        if config.neighborhood_file_path:
            cache_suffix = ".with_hoods.cache"
        cache_path = config.file_path + cache_suffix
        exists = (
            s3client.exists(cache_path)
            if s3client is not None
            else os.path.exists(cache_path)
        )
        if exists:
            get_logger().info("Start load cache file in MapData")
            if s3client is not None:
                map_bytes = s3client.download(cache_path)
                map_data = pickle.loads(map_bytes)
            else:
                with open(cache_path, "rb") as f:
                    map_data = pickle.load(f)
            get_logger().info("Finish load cache file in MapData")
        if map_data is None:
            get_logger().info("No cache file found, start parse pb file in MapData")
            if s3client is not None:
                map_bytes = s3client.download(config.file_path)
                pb = map_pb2.Map().FromString(map_bytes)
            else:
                with open(config.file_path, "rb") as f:
                    pb = map_pb2.Map().FromString(f.read())

            jsons = []
            # add header
            jsons.append(
                {
                    "class": "header",
                    "data": MessageToDict(
                        pb.header,
                        always_print_fields_with_no_presence=True,
                        preserving_proto_field_name=True,
                        use_integers_for_enums=True,
                    ),
                }
            )
            # add aois
            for aoi in pb.aois:
                jsons.append(
                    {
                        "class": "aoi",
                        "data": MessageToDict(
                            aoi,
                            always_print_fields_with_no_presence=True,
                            preserving_proto_field_name=True,
                            use_integers_for_enums=True,
                        ),
                    }
                )
            # add pois
            for poi in pb.pois:
                jsons.append(
                    {
                        "class": "poi",
                        "data": MessageToDict(
                            poi,
                            always_print_fields_with_no_presence=True,
                            preserving_proto_field_name=True,
                            use_integers_for_enums=True,
                        ),
                    }
                )
            if config.neighborhood_file_path:
                get_logger().info("Start load neighborhood file in MapData")
                if s3client is not None:
                    hood_bytes = s3client.download(config.neighborhood_file_path)
                    hood_data = json.loads(hood_bytes)
                else:
                    with open(config.neighborhood_file_path, "r") as f:
                        hood_data = json.load(f)
                get_logger().info("Finish load neighborhood file in MapData")

                if isinstance(hood_data, dict) and "hoods" in hood_data:
                    hood_list = hood_data["hoods"]
                elif isinstance(hood_data, list):
                    hood_list = hood_data
                else:
                    get_logger().error(
                        f"Unexpected neighborhood data format: {type(hood_data)}"
                    )
                    hood_list = []

                get_logger().info(f"Loading {len(hood_list)} neighborhoods")
                for hood in hood_list:
                    jsons.append(
                        {
                            "class": "neighborhood",
                            "data": hood,
                        }
                    )
            map_data = self._parse_map(jsons)
            get_logger().info("Finish parse pb file")
            if not exists:
                get_logger().info("Start save cache file")
                if s3client is not None:
                    s3client.upload(pickle.dumps(map_data), cache_path)
                else:
                    with open(cache_path, "wb") as f:
                        pickle.dump(map_data, f)
                get_logger().info("Finish save cache file")

        self.header: dict = map_data["header"]
        """
        Map metadata, including the following attributes:
        - name (string): Map name, used to identify the semantics of data collections.
        - date (string): Map data creation time.
        - north (float): The coordinate of the northern boundary of the Map data.
        - south (float): The coordinate of the southern boundary of the Map data.
        - east (float): The coordinate of the eastern boundary of the Map data.
        - west (float): The coordinate of the western boundary of the Map data.
        - projection (string): PROJ.4 projection string to support the conversion of xy coordinates to other coordinate systems.
        """

        self.aois: Dict[int, dict] = map_data["aois"]
        """
        AOI collection (aoi) in the map. The dictionary values contain the following attributes:
        - id (int): AOI ID.
        - positions (list[XYPosition]): Shape of polygon.
        - area (float): Area (unit: m2).
        - driving_positions (list[LanePosition]): Connection points to driving lanes in the road network.
        - walking_positions (list[LanePosition]): Connection points to pedestrian lanes in the road network.
        - driving_gates (list[XYPosition]): Position on the AOI boundary corresponding to the connection point to driving lanes.
        - walking_gates (list[XYPosition]): Position on the AOI boundary corresponding to the connection point to pedestrian lanes.
        - urban_land_use (Optional[str]): Urban Land use type, refer to the national standard GB 50137-2011 (https://www.planning.org.cn/law/uploads/2013/1383993139.pdf).
        - poi_ids (list[int]): Contained POI IDs.
        - shapely_xy (shapely.geometry.Polygon): Shape of polygon (in xy coordinates).
        - shapely_lnglat (shapely.geometry.Polygon): Shape of polygon (in latitude and longitude).
        """

        self.pois: Dict[int, dict] = map_data["pois"]
        """
        POI collection (poi) in the map. The dictionary values contain the following attributes:
        - id (int): POI ID.
        - name (string): POI name.
        - category (string): POI category code.
        - position (XYPosition): POI position.
        - aoi_id (int): AOI ID to which the POI belongs.
        """

        self.neighborhoods: Dict[int, dict] = map_data.get("neighborhoods", {})
        """
        Neighborhood collection in the map.
        """

        (
            self._aoi_tree,
            self._aoi_list,
            self._poi_tree,
            self._poi_list,
            self._neighborhood_tree,
            self._neighborhood_list,
        ) = self._build_geo_index()

        self.poi_cate = POI_CATG_DICT

    def get_all_aois(self):
        return self._aoi_list

    def get_all_neighborhoods(self):
        return self._neighborhood_list

    def get_neighborhood(self, neighborhood_id: int):
        return self.neighborhoods[neighborhood_id]

    def get_aoi(self, aoi_id: int):
        return self.aois[aoi_id]

    def get_all_pois(self):
        return self._poi_list

    def get_poi(self, poi_id: int):
        return self.pois[poi_id]

    def _parse_map(self, m: List[Any]) -> Dict[str, Any]:
        # client = MongoClient(uri)
        # m = list(client[db][coll].find({}))
        get_logger().info("Start parse map data")
        header = None
        aois = {}
        pois = {}
        neighborhoods = {}
        for d in m:
            if "_id" in d:
                del d["_id"]
            t = d["class"]
            data = d["data"]
            if t == "neighborhood":
                neighborhoods[data["id"]] = data
            elif t == "aoi":
                aois[data["id"]] = data
            elif t == "poi":
                pois[data["id"]] = data
            elif t == "header":
                header = data
        assert header is not None, "header is None"
        get_logger().info("Finish parse map data - classify")
        projector = pyproj.Proj(header["projection"])  #
        # Process AOI geometries
        get_logger().info("Start process aoi geos")
        for aoi in aois.values():
            if "area" not in aoi:
                # Not a polygon AOI
                aoi["shapely_xy"] = Point(
                    aoi["positions"][0]["x"], aoi["positions"][0]["y"]
                )
            else:
                aoi["shapely_xy"] = Polygon(
                    [(one["x"], one["y"]) for one in aoi["positions"]]
                )
            xys = np.array([[one["x"], one["y"]] for one in aoi["positions"]])
            lngs, lats = projector(xys[:, 0], xys[:, 1], inverse=True)
            lnglat_positions = list(zip(lngs, lats))
            if "area" not in aoi:
                aoi["shapely_lnglat"] = Point(lnglat_positions[0])
            else:
                aoi["shapely_lnglat"] = Polygon(lnglat_positions)
        get_logger().info("Finish process aoi geos in MapData")
        # Process POI geometries
        get_logger().info("Start process poi geos in MapData")
        get_logger().info(f"Total pois to process: {len(pois)}")
        for poi in pois.values():
            point = Point(poi["position"]["x"], poi["position"]["y"])
            poi["shapely_xy"] = point
            lng, lat = projector(point.x, point.y, inverse=True)
            poi["shapely_lnglat"] = Point([lng, lat])
        get_logger().info("Finish process poi geos")

        # Process neighborhood geometries
        get_logger().info("Start process neighborhood geos in MapData")
        for hood in neighborhoods.values():
            positions = hood.get("positions", [])
            if positions:
                hood["shapely_xy"] = Polygon(
                    [(one["x"], one["y"]) for one in positions]
                )
                xys = np.array([[one["x"], one["y"]] for one in positions])
                lngs, lats = projector(xys[:, 0], xys[:, 1], inverse=True)
                hood["shapely_lnglat"] = Polygon(list(zip(lngs, lats)))
            else:
                hood["shapely_xy"] = Point(0, 0)
                hood["shapely_lnglat"] = Point(0, 0)
        get_logger().info("Finish process neighborhood geos in MapData")

        return {
            "header": header,
            "aois": aois,
            "pois": pois,
            "neighborhoods": neighborhoods,
        }

    def _build_geo_index(self):
        # poi:
        # {
        #     "id": 700000000,
        #     "name": "China Telecom (Internet Mobile Phone Store)",
        #     "category": "131300",
        #     "position": {
        #       "x": 448802.148620172,
        #       "y": 4412128.118718166
        #     },
        #     "aoi_id": 500018954,
        # }
        get_logger().info("Start build geo index in MapData")
        aoi_list = list(self.aois.values())
        aoi_tree = shapely.STRtree([aoi["shapely_xy"] for aoi in aoi_list])
        poi_list = list(self.pois.values())
        poi_tree = shapely.STRtree([poi["shapely_xy"] for poi in poi_list])
        neighborhood_list = list(self.neighborhoods.values())
        neighborhood_tree = None
        if neighborhood_list:
            neighborhood_tree = shapely.STRtree(
                [hood["shapely_xy"] for hood in neighborhood_list]
            )
        get_logger().info("Finish build geo index in MapData")
        return (
            aoi_tree,
            aoi_list,
            poi_tree,
            poi_list,
            neighborhood_tree,
            neighborhood_list,
        )

    @overload
    def query_pois(
        self,
        center: Union[Tuple[float, float], Point],
        radius: Optional[float] = None,
        category_prefix: Optional[str] = None,
        limit: Optional[int] = None,
        return_distance: Literal[False] = False,
    ) -> List[Any]: ...

    @overload
    def query_pois(
        self,
        center: Union[Tuple[float, float], Point],
        radius: Optional[float] = None,
        category_prefix: Optional[str] = None,
        limit: Optional[int] = None,
        return_distance: Literal[True] = True,
    ) -> List[Tuple[Any, float]]: ...

    def query_pois(
        self,
        center: Union[Tuple[float, float], Point],
        radius: Optional[float] = None,
        category_prefix: Optional[str] = None,
        limit: Optional[int] = None,
        return_distance: bool = True,
    ) -> Union[List[Tuple[Any, float]], List[Any]]:
        """
        Query the POIs whose categories satisfy the prefix within the specified radius of the center point (sorted by distance).

        Args:
        - center (x, y): Center point (xy coordinate system).
        - radius (float, optional): Radius (unit: m). If not provided, all pois within the map will be returned.
        - category_prefix (str, optional): Category prefix, if the actual category is 100000, then the matching prefix can be 10, 1000, etc.
        - limit (int, optional): The maximum number of POIs returned, sorted by distance, closest ones first (default to None).
        - return_distance (bool): Return the distance or not.

        Returns:
        - Union[List[Tuple[Any, float]],List[Any]]: poi list, each element is (poi, distance) or poi.
        """
        if not isinstance(center, Point):
            center = Point(center)
        if radius is None:
            if return_distance:
                pois = [(p, center.distance(p["shapely_xy"])) for p in self._poi_list]
                get_logger().debug(f"No Radius, all pois with distance. Category prefix: {category_prefix}. pois[:10]: {pois[:10]}")
            else:
                pois = [p for p in self._poi_list]
                get_logger().debug(f"No Radius, all pois. Category prefix: {category_prefix}. pois[:10]: {pois[:10]}")
        else:
            # Get POIs within radius
            indices = self._poi_tree.query(center.buffer(radius))
            # Filter out POIs that do not match the category prefix
            pois = []
            possible_pois = []
            for index in indices:
                poi = self._poi_list[index]
                possible_pois.append(poi)
                if (category_prefix is None) or (category_prefix in poi["category"]):
                    if return_distance:
                        distance = center.distance(poi["shapely_xy"])
                        pois.append((poi, distance))
                    else:
                        pois.append(poi)
            get_logger().debug(f"Radius, filtered pois. Category prefix: {category_prefix}. pois[:10]: {pois[:10]}. Possible pois[:10]: {possible_pois[:10]}")
        if return_distance:
            # Sort by distance
            pois = sorted(pois, key=lambda x: x[1])
        if limit is not None:
            pois = pois[:limit]
        return pois

    def get_poi_cate(self):
        return self.poi_cate

    def get_map_header(self):
        return self.header

    def get_projector(self):
        return self.header["projection"]

    def query_aois(
        self,
        center: Union[Tuple[float, float], Point],
        radius: float,
        urban_land_uses: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Tuple[Any, float]]:
        """
        Query the AOIs whose urban land use within the specified radius of the center point meets the conditions (sorted by distance).

        Args:
        - center (x, y): Center point (xy coordinate system).
        - radius (float): Radius (unit: m).
        - urban_land_uses (List[str], optional): Urban land use classification list, refer to the national standard GB 50137-2011.
        - limit (int, optional): The maximum number of AOIs returned, sorted by distance, closest ones first (default to None).

        Returns:
        - List[Tuple[Any, float]]: aoi list, each element is (aoi, distance).
        """

        if not isinstance(center, Point):
            center = Point(center)
        # Get AOIs within radius
        indices = self._aoi_tree.query(center.buffer(radius))
        # Filter out AOIs that do not meet urban land use conditions
        aois = []
        for index in indices:
            aoi = self._aoi_list[index]
            if (
                urban_land_uses is not None
                and aoi["urban_land_use"] not in urban_land_uses
            ):
                continue
            distance = center.distance(aoi["shapely_xy"])
            aois.append((aoi, distance))
        # Sort by distance
        aois = sorted(aois, key=lambda x: x[1])
        if limit is not None:
            aois = aois[:limit]
        return aois

    def query_neighborhood_by_point(
        self, point: Union[Tuple[float, float], Point]
    ) -> Optional[dict]:
        if self._neighborhood_tree is None:
            return None

        if not isinstance(point, Point):
            point = Point(point)
        indices = self._neighborhood_tree.query(point)
        for index in indices:
            hood = self._neighborhood_list[index]
            if hood["shapely_xy"].contains(point):
                return hood
        return None

    def query_neighborhoods(
        self, center: Union[Tuple[float, float], Point], radius: float
    ) -> List[Tuple[dict, float]]:
        if self._neighborhood_tree is None:
            return []

        if not isinstance(center, Point):
            center = Point(center)

        indices = self._neighborhood_tree.query(center.buffer(radius))
        hoods = []
        for index in indices:
            hood = self._neighborhood_list[index]
            distance = center.distance(hood["shapely_xy"])
            if distance <= radius:
                hoods.append((hood, distance))
        return sorted(hoods, key=lambda x: x[1])