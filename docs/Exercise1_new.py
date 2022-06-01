 ### This program creates a fishnet of points along boundaries

import arcpy
import xlrd
import fnmatch
from os import listdir
from xlrd import open_workbook, cellname
from arcpy import env
from arcpy.sa import *
import os
import glob
import csv
import sys, string, os, arcgisscripting

arcpy.env.overwriteOutput=True
arcpy.SetLogHistory(False)

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

# Paths
path_dir= "C:/Users/1488512/Andre Dropbox/Andre Gröger/Teaching/Spatial Econ/exercises/3. Inference"
path_hist = path_dir+ "/" + "History" 
path_sat = path_dir + "/" + "Satellite"

env.workspace = path_dir + "/" + "Temp"

# Input

input_china=path_hist + "/China_admin_1080.shp"
input_satellite=path_sat + "/Nightlight_2013.tif"
output_distance="distance.dbf"
output_points="points.dbf"

# Repair the possible issues in initial shapefile (e.g., empty features)
arcpy.RepairGeometry_management(in_features=input_china, delete_null="DELETE_NULL")

############# Create the boundaries and a set of points along the boundary ###################

# Dissolve polygons/counties if they have the same status in 1080
arcpy.Dissolve_management(in_features="China_admin_1080", out_feature_class="in_memory/China_adm_1080_dissolve", dissolve_field="H_SUP_PROV", statistics_fields="", multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

# Create the boundaries between polygons
arcpy.PolygonToLine_management(in_features="China_adm_1080_dissolve", out_feature_class="in_memory/China_adm_1080_polyline", neighbor_option="IDENTIFY_NEIGHBORS")

# Create a buffer of 20 kms around the boundaries
arcpy.Buffer_analysis(in_features="China_adm_1080_polyline", out_feature_class="in_memory/China_adm_1080_polyline_buffer", buffer_distance_or_field="20 Kilometers", line_side="FULL", line_end_type="ROUND", dissolve_option="NONE", dissolve_field="", method="PLANAR")

# Create points along the boundaries (non-parametric specification)
arcpy.GeneratePointsAlongLines_management(Input_Features="China_adm_1080_polyline", Output_Feature_Class="in_memory/China_adm_1080_points", Point_Placement="DISTANCE", Distance="40 Kilometers", Percentage="", Include_End_Points="")

############# Create a fishnet of points which will be units of observations ###################

# Create a fishnet of points (same resolution as the satellite data)
# arcpy.CreateFishnet_management(out_feature_class="in_memory/fishnet", origin_coord="102 27", y_axis_coord="102 37", cell_width="0.1", cell_height="0.1", number_rows="", number_columns="", corner_coord="117 41", labels="LABELS", template="102 27 117 41", geometry_type="POLYLINE")
# arcpy.CreateFishnet_management(out_feature_class="in_memory/fishnet", origin_coord="73.55 18.15", y_axis_coord="73.55 28.15", cell_width="0.1", cell_height="0.1", number_rows="", number_columns="", corner_coord="134.77 53.56", labels="LABELS", template="China_admin_1080", geometry_type="POLYLINE")
arcpy.CreateFishnet_management(out_feature_class="in_memory/fishnet", origin_coord="16200276,1505 2009464,315", y_axis_coord="16200276,1505 2009474,315", cell_width="10000", cell_height="10000", number_rows="", number_columns="", corner_coord="21277575,7773 6009564,7999", labels="LABELS", template="16200276,1505 2009464,315 21277575,7773 6009564,7999", geometry_type="POLYLINE")

# Join with the buffer of 20 kms around the boundaries to select the relevant points
fieldmappings=arcpy.FieldMappings()
fieldmappings.addTable("fishnet_label")
fieldmappings.addTable("China_adm_1080_polyline_buffer")
arcpy.SpatialJoin_analysis(target_features="fishnet_label", join_features="China_adm_1080_polyline_buffer", out_feature_class="in_memory/fishnet_label_buffer", join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_COMMON", field_mapping=fieldmappings, match_option="INTERSECT", search_radius="", distance_field_name="")

# Join with the initial administrative shapefile to add the administrative characteristics
fieldmappings=arcpy.FieldMappings()
fieldmappings.addTable("fishnet_label_buffer")
fieldmappings.addTable(input_china)
arcpy.SpatialJoin_analysis(target_features="fishnet_label_buffer", join_features=input_china, out_feature_class="in_memory/fishnet_label_buffer_adm", join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_COMMON", field_mapping=fieldmappings, match_option="WITHIN", search_radius="", distance_field_name="")

# Project


arcpy.DefineProjection_management(in_dataset="fishnet_label_buffer_adm", coor_system="PROJCS['Xian_1980_GK_Zone_19',GEOGCS['GCS_Xian_1980',DATUM['D_Xian_1980',SPHEROID['Xian_1980',6378140.0,298.257]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Gauss_Kruger'],PARAMETER['False_Easting',19500000.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',111.0],PARAMETER['Scale_Factor',1.0],PARAMETER['Latitude_Of_Origin',0.0],UNIT['Meter',1.0]]")

# Add the values taken by the satellite raster at the point location
arcpy.gp.ExtractValuesToPoints_sa("fishnet_label_buffer_adm", input_satellite, "in_memory/fishnet_label_buffer_adm_sat", "NONE", "VALUE_ONLY")

# Add the latitude/longitude
arcpy.AddXY_management(in_features="fishnet_label_buffer_adm_sat")

############# "Merge" the fishnet with the boundary points ###################

# Calculate distance
arcpy.Near_analysis(in_features="fishnet_label_buffer_adm_sat", near_features="China_adm_1080_points", search_radius="20 Kilometers", location="NO_LOCATION", angle="NO_ANGLE", method="PLANAR")

# Export the final table
arcpy.TableToTable_conversion(in_rows="fishnet_label_buffer_adm_sat", out_path=path_dir, out_name="points.dbf")


