# Script to Analyse DROID reports
# parts of the code are taken from and/or inspired by Freud (https://github.com/digital-preservation/freud 
# (Copyright (c) 2019, The National Archives)
# The original version of this script is: https://github.com/adsd-digital/pre-ingest-workflow/blob/main/format-categorization.py

import pandas as pd
import numpy as np
import os
import json

# below loads the csv file into pandas and takes required columns, additional columns for multiple identification are not taken yet as this breaks the csv read. 
# It also asks for the archifiltre prefix and loads a copy of the format-list.csv
output_dir = input("Enter path to output folder of sf_droid_jhove.py:")
output_dir = output_dir.strip(' ').strip('"').strip("'")
csvraw = ""
file_list = os.listdir(output_dir)
#print(file_list)
found_droid_output = False
n = 0
possible_droid_files = ['droid_sf_jhove.csv', 'droid_sf_compare.csv', 'droid_sf.csv', 'droid_complete.csv']

while not found_droid_output and n < 3:
    if not possible_droid_files[n] in file_list:
        #print('x')
        n += 1
    else:
         found_droid_output = True
         csvraw = possible_droid_files[n]
if not found_droid_output:
    "Could not find output file of decomp_droid_sf_jhove.py-script. Will now check for any csv file with 'droid' in its name."
    for name in file_list:
        print(name)
        print(name.find("droid"))
        print(name.endswith('.csv'))
        if (name.find("droid") > -1) and name.endswith('.csv'):
            csvraw = name

csvraw = os.path.join(output_dir, csvraw)
if not os.path.isfile(csvraw):
    print("The script expects there to be a csv file with droid output that has 'droid' in its name in the folder.")
    quit()

print(f"The script will use {csvraw} as its input file.")


do_archifiltre = False

archifiltre_json = ''
for filename in file_list:
    if filename.endswith('.json'):
        archifiltre_json = os.path.join(output_dir, filename)

if archifiltre_json != '':
    print(f"The script will use {archifiltre_json} as archifiltre json.")
    do_archifiltre = True
else:
    print(f'No archifiltre.json found.')

if do_archifiltre:
    archifiltre_prefix = input("Enter the prefix that has to be removed for the archifiltre json.")
else:
    archifiltre_prefix = ""



# columns_needed = ['ID','PARENT_ID','URI','FILE_PATH','NAME','METHOD','STATUS','SIZE','TYPE','EXT','LAST_MODIFIED',
#                   'EXTENSION_MISMATCH','FORMAT_COUNT','PUID','MIME_TYPE','FORMAT_NAME','FORMAT_VERSION',
#                   'sf_id', 'sf_warning','sf_errors', 'sf_EQ_droid', 'jh_RepMod', 'jh_status', 'jh_error', 'jh_error_id']
csv = pd.read_csv(csvraw, low_memory=False)
droidname = os.path.basename(csvraw)
droidname = droidname.rstrip('.csv')

# delimiter for this csv file is currently semicolon - if the csv is with commas (as the DROID output is) the delimiter parameter can be dropped)
formatlist = pd.read_csv('format-list.csv')

# TODO check if format-lst.csv is there and vlaid


def format_categorization():

    #Output file
#    formatcat = pd.ExcelWriter(droidname + '_categorization.xlsx', engine='xlsxwriter')

    #entire droid file as input, adding "Category" columns (has to exist for condition checking)
    all = csv
    all.loc[3, 'Category'] = ''
      
    #establish lists according to column names in format-list.csv
    appraisalList = formatlist['appraisal hint'].values.tolist()
    unchangedList = formatlist['unchanged'].values.tolist()
    autoMigList = formatlist['automatic migration'].values.tolist()
    manMigList = formatlist['manual migration'].values.tolist()
    noOpenList = formatlist['cannot be opened'].values.tolist()
    deleteList = formatlist['delete'].values.tolist()
    protectedList = formatlist['password protected'].values.tolist()
    compressedList = formatlist['compressed'].values.tolist()
    researchList = formatlist['research started'].values.tolist()
    unknownList = formatlist['not categorized yet'].values.tolist()


    # Lists for generation of tags for archifiltre and as base for deletion script
    deletionList = []
    appraisalArchifiltreList = []

    # row by row: PUID is compared to labels in formatliste and assigned a Category
    for i in range(len(all)):
        # if row is not a Folder...
        if all.TYPE[i] != 'Folder':

            # formats that have not been identified are categorized
            if (all.loc[i, 'EXTENSION_MISMATCH']):
                all.loc[i, 'Category'] = 'Extension Mismatch'

            if all.loc[i, 'FORMAT_COUNT'] != 1:
                all.loc[i, 'Category'] = 'No reliable format id'

            # empty files are classed as deletable
            if all.loc[i, 'SIZE'] == 0:
                all.loc[i, 'Category'] = 'delete because empty'
                all.loc[i, 'Deletion'] = 'TRUE'
                delKand = all.loc[i, 'FILE_PATH']
                # print(delKand)
                deletionList.append(delKand)


            # all files with a puid that have not been categorized above are categorized according
            # to format-list.csv
            puid = all.loc[i, 'PUID']
            if (not pd.isna(puid) and pd.isna(all.loc[i, 'Category'])):

                if puid in appraisalList:
                    all.loc[i, 'Appraisal'] = 'appraisal hint'
                    appraisalKand = all.loc[i, 'FILE_PATH']
                    appraisalKand = str.replace(appraisalKand, '\\', '/')
                    appraisalKand = appraisalKand[len(archifiltre_prefix):]
                    appraisalKandFolder = appraisalKand[:appraisalKand.rfind('/')]
                    appraisalArchifiltreList.append(appraisalKand)
                    appraisalArchifiltreList.append(appraisalKandFolder)

                if puid in deleteList:
                    all.loc[i, 'Category'] = 'delete'
                    all.loc[i, 'Deletion'] = 'TRUE'
                    delKand = all.loc[i, 'FILE_PATH']
                    deletionList.append(delKand)
                elif puid in unchangedList:
                    all.loc[i, 'Category'] = 'unchanged'
                elif puid in autoMigList:
                    all.loc[i, 'Category'] = 'automatic migration'
                elif puid in manMigList:
                    all.loc[i, 'Category'] = 'manual migration'
                elif puid in noOpenList:
                    all.loc[i, 'Category'] = 'cannot be opened'
                elif all['PUID'][i] in protectedList:
                    all.loc[i, 'Category'] = 'password protected'
                elif puid in compressedList:
                    all.loc[i, 'Category'] = 'compressed'
                elif puid in researchList:
                    all.loc[i, 'Category'] = 'research started'
                elif puid in unknownList:
                    all.loc[i, 'Category'] = 'format not categorized'

    format_cat_csv = os.path.join(output_dir, 'format_cat.csv')
    all.to_csv(format_cat_csv, index=False)

    if do_archifiltre:
    # generation of tags for archifiltre  
        appraisaltag = {"4e158817-f884-450f-aa89-9e2ef90ea172": { "ffIds": appraisalArchifiltreList,
                                                            'id': "4e158817-f884-450f-aa89-9e2ef90ea172",
                                                            "name": "Bewertungshinweise"

                                                            }
                  }


        appraisaltag = json.dumps(appraisaltag, ensure_ascii=False)

        archifiltre_name = os.path.basename(archifiltre_json)
        archifiltre_name = archifiltre_name[:archifiltre_name.find('.json')]
        archifiltre_json_mod = os.path.join(output_dir, f'{archifiltre_name}_with_tags.json')

        # tagfile = open(appraisaltag)
        tagdata = json.loads(appraisaltag)

        archifiltre_file = open(archifiltre_json)
        archi_data = json.load(archifiltre_file)
        archi_data['tags'] = tagdata

        with open(archifiltre_json_mod, "w") as mod_file:
            json.dump(archi_data, mod_file)

    # generation of file with list of files that are to be deleted
    delete_csv = os.path.join(output_dir, f'delete.csv')
    with open(delete_csv, "w", encoding='utf-8') as g:
        g.write('path to deletable file\n')
        for i in deletionList:
            g.write(i + '\n')

format_categorization()


