only tested on Ubuntu 24.04

## What these scripts do

### decomp_droid_sf_jhove.py

This script executes a series of actions on an input folder that can be helpful in a pre-ingest process for digital preservation:
- decompression of compressed files (at the moment zip, 7z and tar (gzip, bz2 and lzma) are supported.)
- file identification with droid
- file identification with siegfried
- file validation with jhove

### format-categorization.py
Based on PUIDs this script assigns needed actions (e.g. manual migration, deletion) or appraisal hints as they are configured in a csv file to a list of files. The script can also deliver tags that can later be inserted into the output of an archifiltre json. That way e.g. appraisal hints can be viewed in a visualistion of the directory in archifiltre.
The output folder of decomp_droid_sf_jhove.py can serve as input for format-categorization.py

## Prerequisites

For running decomp_droid_sf_jhove.py [droid]([url](https://www.nationalarchives.gov.uk/information-management/manage-information/preserving-digital-records/droid/)), [siegfried]([url](https://github.com/richardlehane/siegfried)) and [jhove]([url](https://jhove.openpreservation.org/getting-started/)) need to be installed.
This script assumes that these programmes are called by "droid", "sf" or "jhove". If these programmes are called by their filepath or another name, these paths/names have to be set in the script decomp_sf_jhove_droid.py in lines 17-19

Both scripts (decomp_droid_sf_jhove.py and format-categorization.py) use a few modules that often don't come preinstalled, among them :
- lxml
- py7zr
- pandas

## Running the scripts:

### decomp_droid_sf_jhove.py

#### set-up
You can simply run the script by typing
```
python decomp_droid_sf_jhove.py
```
The script will start a dialogue for setting up a few configurations.
You need to tell the script the path to the input folder and ad lib the path to the output folder.
You can then choose between the following options:
1. Only decompressing
2. Only Format identification with Droid
3. Only Format identification with Droid and Siegfried
4. Format Identification and Validation (with Jhove, if Droid and Siegfried have the same result)
5. Decompressing and Format identification with Droid and Siegfried
6. Everything (Decompressing, Format identification and Validation). \n")

According to this choice the script will ask a few other configuration decisions. 

#### jhove-config.csv 
If you choose jhove validation the script will check if a jhove-conig.csv is provided in the directory that the script is started from. If not it will ask you if you want to provide one. 
If you do not want to rely on jhove choosing the right module for the submitted file you need to configure this csv.

This jhove config file needs to be a csv file with two columns, the first one called "PUID", the second one "jhove_module". In the first column puids can be listed for which jhove should choose a specific module.
For files with puids that are not listed in the csv the script will use the module that jhove autodetects.

#### output

The script will always create a report.txt in the output folder with an overview of the executed actions.
Beyond that, the output depends on the chosen config options:

##### decompressing
Droid will look for compressed files, based on a list of file extensions. The script then tries to decompress those formats that it should be able to. 

If there already is a folder of the same name as 
the compressed folder it creates a new folder that adds the 'suffix _decomp' to the original name. 
If within the compressed package files are found that do not belong to a 
folder, the compressed file is unpacked to a newly created folder with the name of the compressed file with the suffix '_folderlevel_by_script'.

In the output folder the script will store the droid csv with the list of the compressed files
and a csv file in a log folder where the filepaths of the detected compressed files and status (success/error) 
for the decompressing process are listed.

##### droid, siegfried, jhove
If only Droid identification is chosen the output is a droid csv. If the identification 
is also done with siegfried columns for the siegfried result, errors and warnings are added and a columns with
True/False values as to whether Siegfried and Droid reached the same conclusion.

If Jhove validation is added to the process for the files where Droid and Siegfried get the
same result a jhove validation is executed. The result of this validation, potential errors and their ID are 
written to the in additional columns of the csv file. The results of the jhove process are also stored as 
xml files in a separate folder.

##### copies of problematic files
If this option is set files with problematic identification or validation results (multiple or no identification, invalid or not well-formed files) 
are copied to separate folders.

### format-categorization.py

#### set-up and expected files

##### droid csv output

After starting the script asks for the path to the output folder of decomp_droid_sf_jhove.py.
It checks this folder for one of the (potentially enriched) droid csv files that decomp_droid_sf_jhove.py has as its output.

The script also works with droid output csvs generated any other way. But at the moment it will only 
check in the directory (if it has not found any of the file names it expects from decomp_droid_sf_jhove) if it finds any file 
that has "droid" in its name and the file extension csv!

##### format list

The script also expects there to be a format list.

The format list needs the following columns:
unchanged, automatic migration, manual migration, cannot be opened, delete, password protected, compressed, research started,
not categorized yet,appraisal hint.

##### prefix for archifiltre

The script generates tags that can be inserted in an archifiltre output. If you want to use these tags 
you need to tell the
script how to shorten the file paths so archifiltre will be able to interpret them: 
    
The file paths in the archifiltre json start with the folder that it received as input.
In DROID the file paths are absolute. So for the file paths to work in archifiltre the folders leading 
    up to the analysed folders have to be removed (but the leading slash needs to be kept). 

As an example: Let's say, the folder "archifolder" has been analysed, in DROID and in archifiltre.
    "archifolder" is placed at /path/to/archifolder. Then you have to input as prefix for archifiltre: "/path/to" (without ").


#### output

This script will analyse the DROID report and categorizes the formats according to
- needs for preparation before ingest
- deletable formats
- hint for appraisal

As output the script creates in the directory which the program is running from
1.  A csv file with added columns for
    Category, Deletion and Appraisal,
2.  A csv file with the file paths for all the files that are marked for deletion
3.  A file with the file paths in a tag format that can afterwards be added to the json file that archifiltre 
    (https://github.com/SocialGouv/archifiltre-docs) creates. 

The tags generated as third output can then be manually copied to the json element tags{} in the archifiltre output. 
If you then load this output into archifiltre again the tagged elements should be visible in the visualized folder structure.

