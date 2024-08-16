# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Tool Name: Seafloor Score to Oil Sensitivity - SSOS
# Source Name: seafloor_score_ssos.py
# Created: March, 2023 (Version 1.0)
# Last updated: July 18, 2024 (Version 1.3)
# Author: Enatielly Goes
# Description: Calculates the sensitivity of the seafloor to oil pollution based on the combination of terrain attributes such as standardized bathymetric position indices, rugosity and slope.
# 
# Usage: seafloor_score_ssos <input_broad_bpi> <input_fine_bpi> <input_rugosity> <lower_rugosity> <medium_rugosity> <upper_rugosity> <input_slope> <lower_slope> <medium_slope> <upper_slope> <output_ssos>
#
# Reference: Goes, E.R., Mallmann, D.L.B., Brown, C.J., Maida, M., Ferreira, B.P. and Araújo, T.C.M. (2023) A seafloor sensitivity index to oil spills in tropical marine protected areas. Continental Shelf Research, Volume 266,
# 105069,ISSN 0278-4343, https://doi.org/10.1016/j.csr.2023.105069.
# ---------------------------------------------------------------------------

# Import arcpy module
import arcpy

# Import OS module
import os

# Check if the Temp directory exists and create it if it doesn't
temp_folder = "C:\\Temp"
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)
    arcpy.AddMessage("Directory {} created successfully.".format(temp_folder))
else:
    arcpy.AddMessage("Directory {} already exists.".format(temp_folder))

# Script arguments
input_broad_bpi = arcpy.GetParameterAsText(0)

input_fine_bpi = arcpy.GetParameterAsText(1)

input_rugosity = arcpy.GetParameterAsText(2)

lower_rugosity = arcpy.GetParameterAsText(3)

medium_rugosity = arcpy.GetParameterAsText(4)

upper_rugosity = arcpy.GetParameterAsText(5)

input_slope = arcpy.GetParameterAsText(6)

lower_slope = arcpy.GetParameterAsText(7)

medium_slope = arcpy.GetParameterAsText(8)

upper_slope = arcpy.GetParameterAsText(9)

output_ssos = arcpy.GetParameterAsText(10)


# Define Local variables names and output folder:
output_broad_reclass = os.path.join(temp_folder, "ssos_column1")
output_fine_reclass = os.path.join(temp_folder, "ssos_column2")
output_rugosity_reclass = os.path.join(temp_folder, "ssos_column3")
output_slope_reclass = os.path.join(temp_folder, "ssos_column4")


arcpy.AddMessage("Starting the reclassification processes...")

# Construct the reclassification string based on user-defined thresholds for various terrain attributes.
reclass_values_rugosity = "0 {0} 1;{0} {1} 2;{1} {2} 3;{2} 9999 3".format(lower_rugosity, medium_rugosity, upper_rugosity)
reclass_values_slope = "0 {0} 1;{0} {1} 2;{1} {2} 3;{2} 9999 3".format(lower_slope, medium_slope, upper_slope)

# Process: Reclassify BBPI
arcpy.AddMessage("Reclassifying standardized Broad BPI grid...")
arcpy.gp.Reclassify_sa(input_broad_bpi, "VALUE", "-99999 -49 3;-49 50 1;50 9999 2", output_broad_reclass, "DATA")

# Process: Reclassify FBPI
arcpy.AddMessage("Reclassifying standardized Fine BPI grid...")
arcpy.gp.Reclassify_sa(input_fine_bpi, "VALUE", "-99999 -49 3;-49 50 1;50 9999 2", output_fine_reclass, "DATA")

# Process: Reclassify Rugosity
arcpy.AddMessage("Reclassifying Rugosity by user-defined thresholds...")
arcpy.gp.Reclassify_sa(input_rugosity, "VALUE", reclass_values_rugosity, output_rugosity_reclass, "DATA")

# Process: Reclassify Slope
arcpy.AddMessage("Reclassifying Slope by user-defined thresholds...")
arcpy.gp.Reclassify_sa(input_slope, "VALUE", reclass_values_slope, output_slope_reclass, "DATA")

# Process: Combine to index
# Combine input rasters
arcpy.gp.Combine_sa(";".join([output_broad_reclass, output_fine_reclass, output_rugosity_reclass, output_slope_reclass]), output_ssos)

# Process: Add Field
arcpy.AddField_management(output_ssos, "SSOS", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

# Process: Calculate Field
arcpy.AddMessage("Calculating SSOS index...")

# Define a code block that includes the mode function for SSOS calculation
codeblock_ssos = """
def mode(lst):
    from collections import Counter
    return Counter(lst).most_common(1)[0][0]
"""

# Execute the CalculateField management using the mode function for SSOS calculation
arcpy.CalculateField_management(
    output_ssos,
    "SSOS",
    "mode([!SSOS_COLUMN1!, !SSOS_COLUMN2!, !SSOS_COLUMN3!, !SSOS_COLUMN4!])",
    "PYTHON_9.3",
    codeblock_ssos
)


# Process: Delete Field
arcpy.DeleteField_management(output_ssos, "SSOS_COLUMN4;SSOS_COLUMN3;SSOS_COLUMN2;SSOS_COLUMN1")


# Finalizing the processing and cleaning up temporary data and resources to ensure optimal performance and data integrity.
arcpy.AddMessage("Finalizing processing and cleaning up temporary files...")

try:
    arcpy.Delete_management(output_broad_reclass)
    arcpy.Delete_management(output_fine_reclass)
    arcpy.Delete_management(output_rugosity_reclass)
    arcpy.Delete_management(output_slope_reclass)
    arcpy.AddMessage("Temporary files deleted successfully.")
except Exception as e:
    arcpy.AddError("Failed to delete temporary files: " + str(e))


# Simple calculation to determine the percentage representation of each sensitivity class in relation to oil pollution

# Initialize counters for all necessary sensitivity classes and for the total pixel count.
total_pixels = 0
class_1_pixels = 0
class_2_pixels = 0
class_3_pixels = 0

# Utilize a search cursor to iterate over records in the attribute table
with arcpy.da.SearchCursor(output_ssos, ["SSOS", "COUNT"]) as cursor:
    for row in cursor:
        total_pixels += row[1]  # Somar todos os pixels
        if int(row[0]) == 1:
            class_1_pixels += row[1]  # Increment the counter for pixels classified as low sensitivity each time one is encountered during the dataset iteration.
        elif int(row[0]) == 2:
            class_2_pixels += row[1]  # Increment the counter for pixels classified as medium sensitivity each time one is encountered during the dataset iteration.
        elif int(row[0]) == 3:
            class_3_pixels += row[1]  # Increment the counter for pixels classified as high sensitivity each time one is encountered during the dataset iteration.

# Calculate and display the percentages for each sensitivity class
if total_pixels > 0:
    percentage_class_1 = (class_1_pixels / float(total_pixels)) * 100
    percentage_class_2 = (class_2_pixels / float(total_pixels)) * 100
    percentage_class_3 = (class_3_pixels / float(total_pixels)) * 100
    arcpy.AddMessage("    ")
    arcpy.AddMessage("Percentage of SSOS classes:")
    arcpy.AddMessage("Percentage of low sensitivity: {:.2f}%".format(percentage_class_1))
    arcpy.AddMessage("Percentage of medium sensitivity: {:.2f}%".format(percentage_class_2))
    arcpy.AddMessage("Percentage of high sensitivity: {:.2f}%".format(percentage_class_3))
    arcpy.AddMessage("    ")
else:
    arcpy.AddMessage("No pixels found in the raster.")

# Final message
arcpy.AddMessage("Process for SSOS is successfully completed.")
