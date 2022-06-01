import arcpy
>>> import arcpy
... import xlrd
... import fnmatch
... from os import listdir
... from xlrd import open_workbook, cellname
... from arcpy import env
... from arcpy.sa import *
... import os
... import glob
... import csv
... import sys, string, os, arcgisscripting
... 
... arcpy.env.overwriteOutput=True
... arcpy.SetLogHistory(False)
... 
... # Check out any necessary licenses
... arcpy.CheckOutExtension("spatial")
... 
... # Paths
... path_dir= "C:/Users/1488512/Andre Dropbox/Andre Gröger/Teaching/Spatial Econ/exercises/3. Inference"
... path_elevation = path_dir+ "/" + "Elevation" 
... path_no2 = path_dir + "/" + "No2"
... path_airfields = path_dir + "/" + "Airfields"
... path_ps = path_dir + "/" + "PS"
... path_adm = path_dir + "/" + "Administrative"
... path_temp = path_dir + "/" + "Temp"
... 
... env.workspace = path_dir + "/" + "Temp"
... 
... # Input
... input_china=path_adm + "/CHN_adm3.shp"
... input_elevation=path_elevation + "/Elevation.tif"
... input_no2=path_no2 + "/no2_201603.grd"
... input_airfields=path_airfields + "/Airfields.shp"
... input_ps=path_ps + "/PS.shp"
... 
... # Output
... output_slope=path_temp + "/Slope.tif"
... 
... # Function
... def clearLayers():
...     mxd = arcpy.mapping.MapDocument('CURRENT')
...     for df in arcpy.mapping.ListDataFrames(mxd):
...         for lyr in arcpy.mapping.ListLayers(mxd, "", df):
...             arcpy.mapping.RemoveLayer(df, lyr) 
...     del mxd
... 
... # Fishnet clipped on administrative China
... arcpy.CreateFishnet_management(out_feature_class="in_memory/fishnet", origin_coord="73.55770111084 18.1593055725098", y_axis_coord="73.55770111084 28.1593055725098", cell_width="0.4", cell_height="0.4", number_rows="", number_columns="", corner_coord="134.77392578125 53.5608596801759", labels="LABELS", template="", geometry_type="POLYLINE")
... arcpy.AddXY_management(in_features='fishnet_label')
... arcpy.Delete_management(in_data='fishnet', data_type="GPFeatureLayer")
... for field in ['POINT_X','POINT_Y']:
... 	arcpy.AddField_management(in_table="fishnet_label", field_name=field+"_fishnet", field_type="DOUBLE")
... 	arcpy.CalculateField_management(in_table="fishnet_label", field=field+"_fishnet", expression="["+field+"]", expression_type="VB",code_block="")
... 
... fieldmappings=arcpy.FieldMappings()
... fieldmappings.addTable('fishnet_label')
... fieldmappings.addTable(input_china)
... arcpy.SpatialJoin_analysis(target_features="fishnet_label", join_features=input_china, out_feature_class=path_temp+"/fishnet_label_adm", join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_COMMON", field_mapping=fieldmappings, match_option="INTERSECT", search_radius="", distance_field_name="")
... 
... for layer in ["fishnet_label","fishnet"]:
... 	arcpy.Delete_management(in_data=layer, data_type="GPFeatureLayer")
... 
... # Prepare pollution sources
... for source in ['Airfields','PS']:
... 	arcpy.CopyFeatures_management(in_features=path_dir + "/" +source + "/" +source+".shp",out_feature_class="in_memory/"+source)
... 	arcpy.AddXY_management(in_features="in_memory/"+source)
... 	for field in ['POINT_X','POINT_Y']:
... 		arcpy.AddField_management(in_table="in_memory/"+source, field_name=field+"_"+source, field_type="DOUBLE")
... 		arcpy.CalculateField_management(in_table="in_memory/"+source, field=field+"_"+source, expression="["+field+"]", expression_type="VB",code_block="")
... 		arcpy.DeleteField_management(in_table="in_memory/"+source, drop_field=field)
... 
... clearLayers()
... 		
... # Slope
... arcpy.gp.Slope_sa(input_elevation, output_slope, "DEGREE", "0.00000956")
... arcpy.gp.RasterCalculator_sa(""""Slope.tif"/2+1""", "in_memory/cost_wind")
... 
... # Isolate single pollution sources and calculate sender/receiver distance (add latitude/longitude)
... for source in ['Airfields','PS']:
... 	rows = arcpy.SearchCursor("in_memory/"+source)
... 	n=1
... 	for row in rows:
... 		out=path_temp+ "/" +source+str(n)
... 		fish=path_temp+"/fishnet_label_adm.shp"
... 		table_cost=path_temp+"/c_"+source[0:2]+str(n)+".csv"
... 		table_dist=path_temp+"/d_"+source[0:2]+str(n)+".dbf"
... 		if n<2:
... 			X = row.getValue("POINT_X_"+source)
... 			Y = row.getValue("POINT_Y_"+source)
... 			point = arcpy.Point(X,Y)
... 			ptGeometry = arcpy.PointGeometry(point)
... 			arcpy.AddXY_management(ptGeometry)
... 			arcpy.gp.CostDistance_sa(ptGeometry, "in_memory/cost_wind", out, "", "", "", "", "", "")
... 			arcpy.gp.ExtractValuesToPoints_sa(fish,out, "in_memory/t_"+source[0:2]+str(n), "NONE", "VALUE_ONLY")
... 			field_names = [field.name.encode('ascii','ignore') for field in arcpy.ListFields("in_memory/t_"+source[0:2]+str(n)) if field.name.startswith("FID") or field.name.startswith("POINT_") or field.name.startswith("ID_") or field.name.startswith("RASTERVALU")]
... 			arcpy.ExportXYv_stats("in_memory/t_"+source[0:2]+str(n),field_names,"COMMA",table_cost,"ADD_FIELD_NAMES")
... 			arcpy.GenerateNearTable_analysis(in_features="in_memory/t_"+source[0:2]+str(n), near_features=ptGeometry, out_table=table_dist, search_radius="",location="LOCATION", angle="NO_ANGLE", closest="CLOSEST", closest_count="0", method="PLANAR")
... 			n=n+1
... 
... # Create actual pollution			
... pollution=path_temp+ "/pollution.csv"
... arcpy.gp.ExtractValuesToPoints_sa(path_temp+"/fishnet_label_adm.shp",input_no2, "in_memory/pollution", "NONE", "VALUE_ONLY")
... field_names = [field.name.encode('ascii','ignore') for field in arcpy.ListFields("in_memory/pollution") if field.name.startswith("FID") or field.name.startswith("POINT_") or field.name.startswith("ID_") or field.name.startswith("RASTERVALU")]
... arcpy.ExportXYv_stats("in_memory/pollution",field_names,"COMMA",pollution,"ADD_FIELD_NAMES")
... 
... clearLayers()			
... 	
