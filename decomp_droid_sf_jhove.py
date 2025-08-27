import csv
import os
import shutil
import subprocess
import tarfile
import traceback
from lxml import etree
from zipfile import ZipFile

import numpy as np
import pandas as pd
import py7zr
from io import StringIO


# TODO set up log

droid_call = 'droid.sh'
jhove_call = 'jhove'
sf_call = 'sf'

def setup_dir(root, dir_name):
    dir_path = os.path.join(root, dir_name)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def check_config_file_exists(configtype, filepath):
    # check existence of file and possibly set other config file
    config_exists = False
    config_path = ""
    if os.path.isfile(filepath):
        config_path = filepath
        config_exists = True
        print(f'{config_path} is used as config file for {configtype}.')
        other_config = input(f'If your want to use another file, please put in filepath here:')
        other_config.strip(" ").strip('"').strip("'")
        if not other_config == "":
            if os.path.isfile(other_config):
                config_path = other_config
                config_exists = True
                print(f'{config_path} is used as config file for {configtype}.')
    else:
        print(f'{filepath} is not an exisiting file.')
        other_config = input(f'If your want to use another file, please put in filepath here:\n ')
#                             f'Otherwise {configtype} will not be executed')
        other_config.strip(" ").strip('"').strip("'")
        if not other_config == "":
            if os.path.isfile(other_config):
                config_path = other_config
                config_exists = True
                print(f'{config_path} is used as config file for {configtype}.')
#        else:
#            print(f'{configtype} will not be executed.')

    return config_exists, config_path

def check_config_valid(columnnames, filepath):
    df_config = pd.read_csv(filepath)
    if columnnames.issubset(df_config.columns):
        return True
    else:
        return False


def setup_config():
    analyze_dir = input("Put in the path to the directory that should be analyzed.\n "
                        "If left empty, current working directory is used.\n")
    analyze_dir = analyze_dir.strip(" ").strip('"').strip("'")
    # print(analyze_dir)
    if not os.path.isdir(analyze_dir):
        # print("Not a directory")
        analyze_dir = os.getcwd()
    print(f"Analyzed folder is {analyze_dir}.")
    output_dir = input(f"Set output directory.\n"
                       f"If left empty the folder {analyze_dir}_output is created "
                       " (if it does not exist already).\n")
    output_dir = output_dir.strip(" ").strip('"').strip("'")
    if not os.path.isdir(output_dir):
        # print(f"{output_dir} is not a directory")
        output_dir = (analyze_dir.rstrip("/") + "_output")
        # print(f"{output_dir}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    print(f"Output-Ordner ist {output_dir}.")



    chosen_workflow = input("Which workflow do you want to execute? Type in the number of the workflow. \n"
                            "(1) Only decompressing. \n"
                            "(2) Only Format identification with Droid. \n"
                            "(3) Only Format identification with Droid and Siegfried. \n"
                            "(4) Format Identification and Validation (with Jhove, if Droid and Siegfried have the same result) \n"
                            "(5) Decompressing and Format identification with Droid and Siegfried. \n"
                            "(6) Everything (Decompressing, Format identification and Validation). \n")
    if int(chosen_workflow) not in range(1, 7):
        # print(type(chosen_workflow))
        # print(type(int(chosen_workflow)))
        # print(chosen_workflow)
        chosen_workflow = input("Input has to be an integer between 1 and 6. Else the script will exit.")
        if not type(chosen_workflow) is int or chosen_workflow not in range(1, 6):
            quit()

    match int(chosen_workflow):
        case 1:
            print('Chosen Workflow: (1) Only decompressing.')
            decomp = True
            droid = False
            sf = False
            jhoving = False
        case 2:
            print('Chosen workflow: (2) Only Format identification with Droid.')
            decomp = False
            droid = True
            sf = False
            jhoving = False
        case 3:
            print('Chosen workflow: (3) Only Format identification with Droid and Siegfried."')
            decomp = False
            droid = True
            sf = True
            jhoving = False
        case 4:
            print('Chosen workflow: (4) Format Identification and Validation (with Jhove, if Droid and Siegfried have the same result).')
            decomp = False
            droid = True
            sf = True
            jhoving = True
        case 5:
            print("Chosen workflow: (5) Decompressing and Format identification with Droid and Siegfried.")
            decomp = True
            droid = True
            sf = True
            jhoving = False
        case 6:
            print("Chosen workflow: (6) Everything (Decompressing, Format identification and Validation).")
            decomp = True
            droid = True
            sf = True
            jhoving = True


    update = False
    hash_set = False
    mk_copies = False
    if int(chosen_workflow) > 1:
        update_yn = input("Do you want to update Droid and siegfried? If yes, please type Y.\n"
                          "Otherwise update will be skipped.")
        if update_yn == "Y":
            update = True
        hash_yn = input("Should droid generate hash sums? Then please type Y.\n"
                        "Default is no.")
        if hash_yn == "Y":
            hash_set = True

    if int(chosen_workflow) > 2:
        copies_yn = input("Do you want the script to generate copies for files with uncertain or incorrect formats?\n "
                          "If yes, please type Y.\n"
                          "Otherwise no copies will be made.")
        if copies_yn == "Y":
            mk_copies = True

    jhove_dir = ""
    jhove_config_exists = ""
    jhove_config = ""

    if jhoving:
        jhove_config_exists, jhove_config = check_config_file_exists('jhove', 'jhove_config.csv')
        if jhove_config_exists:
            if check_config_valid({'PUID','jhove_module'}, jhove_config):
                print('Provided config is valid and will be used.')
            else:
                if jhove_config_exists:
                    print(f'Provided config is not used. The config does not have a column named PUID and another '
                          f'one called "jhove_module. \n'
                          f'Jhove modules are chosen based on jhove guess since no config file was provided.')
                else:
                    print(f'Jhove modules are chosen based on jhove guess since no config file was provided.')

        jhove_dir = os.path.join(output_dir, 'jhove_output')
        if not os.path.exists(jhove_dir):
                os.makedirs(jhove_dir)


    return (analyze_dir, output_dir, update, decomp, droid, hash_set, sf, jhoving, jhove_dir, jhove_config_exists, jhove_config,
            mk_copies)

def check_versions(do_droid, do_sf, do_jhove):
    versions = []
    if do_droid:
        try:
            droid_version = subprocess.check_output([droid_call, '--version'], text = True)
            droid_version = droid_version[:droid_version.find('\n')]
            print(f'Droid version is {droid_version}.')
            versions.append(f'Droid {droid_version}\n')
        except BaseException:
            print('The command "droid --version" could not be executed. Is droid installed? Is the path set correctly?')
            traceback.print_exc()
            quit()
    if do_sf:
        try:
            sf_version = subprocess.check_output([sf_call, '-version'], text=True)
            sf_version = sf_version[:sf_version.find('\n')]
            print(f'Siegfried version is {sf_version}.')
            versions.append(f'{sf_version}\n')
        except BaseException:
            print('The command "sf version" could not be executed. Is siegfried installed? Is the path set correctly?')
            traceback.print_exc()
            #quit()
    if do_jhove:
        try:
            jhove_version = subprocess.check_output([jhove_call, '--version'], text=True)
            jhove_version = jhove_version[:jhove_version.find('\n')]
            print(f'Jhove version is {jhove_version}.')
            versions.append(f'{jhove_version}\n')
            #print(jhove_version)
        except BaseException:
            print('The command "jhove --version" could not be executed. Is jhove installed? Is the path set correctly?')
            traceback.print_exc()
            quit()

    return versions




def droid_sf_update():
    subprocess.run([droid_call, '-d'])
    subprocess.run([sf_call, '-update'])

# TODO: output: nicht entpackte Archive
def droid_compressed(folderinput, droid_output):
    ## TODO: set list for container files that should be tried to unpack
    droidfile = os.path.join(droid_output, "droid_compressed.csv")
    subprocess.run([droid_call,
                    folderinput, '-R', '-ff', 'file_ext any zip 7z xz gz bz2 tgz tar rar', '-f',
                    'type none FOLDER', '-o', droidfile])
    return droidfile

# Aktuell nicht verwendet.
def droid_shutil(comp_path, fold_path):
    # print(comp_path)
    # print(fold_path)
    print(f"Unpacking {comp_path}")
    last_part = comp_path[comp_path.rfind('/')+1:]
    last_part = last_part[:last_part.find('.')]
    fold_path = os.path.join(fold_path, f'{last_part}_folderlevel_by_script')
    try:
        shutil.unpack_archive(comp_path, fold_path)
        print(f"Successfully unpacked to {fold_path}")
        return '?', comp_path, "success"
    except BaseException:
        print(f"ERROR: {comp_path} not successfully unpacked.")
        traceback.print_exc()
        return '?', comp_path, "ERROR"

def droid_untar(tar_path, fold_name):
    print("Untarring " + tar_path)
    try:
        with tarfile.open(tar_path) as mytar:
            free_floating = False
            for i in mytar.getmembers():
                # print(i.name)
                # Check if the member is a file and does not contain a '/'
                if i.isfile() and '/' not in i.name:
                    free_floating = True
                    print(f"{i.name} is a file not contained in a directory.")
                    last_part = mytar.name[mytar.name.rfind('/')+1:]
                    last_part = last_part[:last_part.find('.')]
                    print(last_part)
            if free_floating:
                fold_name = os.path.join(fold_name, f'{last_part}_folderlevel_by_script')
            mytar.extractall(fold_name)
            print(f"Successfully untarred to {fold_name}.")
            return 'tar', tar_path, "success"
    except BaseException:
        print(f"ERROR: {tar_path} not successfully unpacked.")
        traceback.print_exc()
        return 'tar', tar_path, "ERROR"


def droid_unzip(zip_path, fold_name):
    print("Unzipping " + zip_path)
    try:
        with ZipFile(zip_path) as myzip:
            zip_name_list = myzip.namelist()
            free_floating_files = False
            # https://stackoverflow.com/questions/15267661/how-to-check-if-entry-is-file-or-folder-using-pythons-standard-library-zipfile
            for i in zip_name_list:
                if not '/' in i:
                    free_floating_files = True
            if free_floating_files:
                last_part = myzip.filename[myzip.filename.rfind('/')+1:]
                last_part = last_part.strip('.zip')
                fold_name = os.path.join(fold_name, f'{last_part}_folderlevel_by_script')
#                print(fold_name)
            myzip.extractall(path=f'{fold_name}')
            print(f"Successfully unzipped to {fold_name}.")
            return 'zip', zip_path, "success"
    except BaseException:
        print(f"ERROR: {zip_path} not successfully unpacked.")
        traceback.print_exc()
        return 'zip', zip_path, "ERROR"

def droid_un7zip(sevenzip_path, fold_name):
    print("7unzipping " + sevenzip_path)
    try:
        with py7zr.SevenZipFile(sevenzip_path) as my7z:
            #sevenzip_name_list = my7z.namelist()
            sevenzip_list = my7z.list()
            free_floating_files = False
            # https://stackoverflow.com/questions/15267661/how-to-check-if-entry-is-file-or-folder-using-pythons-standard-library-zipfile
            for i in sevenzip_list:
                # print(i.filename)
                if not '/' in i.filename and not i.is_directory:
                    # for i in sevenzip_name_list:
                    #     if not '/'  and i.isdi i:
                    free_floating_files = True
                    # print(free_floating_files)
            if free_floating_files:
                last_part = my7z.filename[my7z.filename.rfind('/')+1:]
                last_part = last_part.strip('.7z')
                fold_name = os.path.join(fold_name, f'{last_part}_folderlevel_by_script')
                # print(fold_name)
            my7z.extractall(path=f'{fold_name}')
            ## TODO: schönerer Output wäre mit Last-part!
            print(f"Successfully un7zipped to {fold_name}.")
            return '7z', sevenzip_path, "success"

    except BaseException:
        print(f"ERROR: {sevenzip_path} not successfully unpacked.")
        traceback.print_exc()
        return '7z', sevenzip_path, "ERROR"


def droid_decomp_routine(droid_input, output_dir):
    #log_dir = setup_dir(output_dir, 'logs')
    decomp_log = os.path.join(output_dir, 'decomp_log.csv')
    with open(decomp_log, mode='w') as csvfile:
        logwriter = csv.writer(csvfile)
        logwriter.writerow(['Type', 'Status', 'Path'])
    comp_types = {"zip": droid_unzip,
                  "tar": droid_untar,
                  "gz": droid_untar,
                  "tgz": droid_untar,
                  "xz": droid_untar,
                  "bz2": droid_untar,
                  "7z": droid_un7zip}
    columns_needed = ['ID', 'PARENT_ID', 'URI', 'FILE_PATH', 'NAME', 'METHOD', 'STATUS', 'SIZE', 'TYPE', 'EXT',
                      'LAST_MODIFIED', 'EXTENSION_MISMATCH', 'FORMAT_COUNT', 'PUID', 'MIME_TYPE', 'FORMAT_NAME',
                      'FORMAT_VERSION']
    sth_to_unpack = False
    try:
        decomp_csv = pd.read_csv(droid_input, usecols=columns_needed)
        sth_to_unpack = True
    except pd.errors.EmptyDataError:
        print("Keine zip, 7z or gz.xz- Dateien gefunden.")
        return ["Keine zip, 7z or gz.xz- Dateien gefunden.\n"]

    # print(sth_to_unpack)

    if sth_to_unpack:
        print(range(len(decomp_csv)))
        for i in range(len(decomp_csv)):
            ext = decomp_csv.loc[i].EXT
            comp_file_path = decomp_csv.loc[i].FILE_PATH
            if not decomp_csv.loc[i].EXTENSION_MISMATCH:
                # print(ext)
                # print(comp_types[ext])
                folder_name = comp_file_path.rstrip("." + ext)
                # Problem: tar.xz -> wenn xz weggenommen wird, immer noch tar, dadurch:
                # schon vorhandener gleichnamiger Ordner nicht erkannt
                if folder_name[-4:] == ".tar":
                    folder_name = folder_name[:-4]
                    ext = 'tar'
                if ext in comp_types:
                    #print(f'folder ist {folder_name}')
                    #folder_name = os.
                    #comp_file_path = f'"{comp_file_path}"'
                    #print(folder_name)
                    folder_exists = False
                    if os.path.exists(folder_name):
                        folder_exists = True
                        folder_name = folder_name + "_decomp"
                        #print(folder_name)
                    else:
                        slash_id = folder_name.rfind("/")
                        folder_name = folder_name[:slash_id + 1]
                    # folder_name = f'{folder_name}_decomp_by_archive_script'
                    type, path, status = comp_types[ext](comp_file_path, folder_name)
                    logarray = [type, status, path]
                    with open(decomp_log, mode='a') as csvfile:
                        logwriter = csv.writer(csvfile)
                        logwriter.writerow(logarray)
                else:
                    print(f"{ext} is not a compression format that can be automatically unpacked by this script.\n"
                          f"Not unpacked file is {comp_file_path}")
                    with open(decomp_log, mode='a') as csvfile:
                        logwriter = csv.writer(csvfile)
                        logwriter.writerow([ext, 'ERROR - no automatic extraction', comp_file_path])

                # TODO bei gleichnamigem Ordner: vergleichen
            # TODO komprimiertes Paket löschen (?)
            else:
                if decomp_csv.loc[i].EXTENSION_MISMATCH:
                    print(f"{comp_file_path} has an Extension Mismatch. Needs to be controlled before extraction.")
                    with open(decomp_log, mode='a') as csvfile:
                        logwriter = csv.writer(csvfile)
                        logwriter.writerow([ext, 'ERROR - Ext Mismatch', comp_file_path])
        df_log = pd.read_csv(decomp_log)
        errors_int = df_log[df_log['Status'] != 'success'].shape[0]
        success_int = df_log[df_log['Status'] == 'success'].shape[0]
        success = f'Successfully unpacked: {success_int}.\n'
        errors = f'Errors while unpacking: {errors_int}.\n\n'
        types = df_log['Type'].unique()
        unpacking_report_info = []
        unpacking_report_info.append(success)
        unpacking_report_info.append(errors)
        for t in types:
            print(f'Compression format {t}: {df_log[df_log['Type'] == t].shape[0]} times\n')
            unpacking_report_info.append(f'Compression format {t}: {df_log[df_log['Type'] == t].shape[0]} times\n')
        return unpacking_report_info

def droid_complete(folder_input, droid_output, hash_generation):
    complete_droid = os.path.join(droid_output, "droid_complete.droid")
    complete_droid_csv = os.path.join(droid_output, "droid_complete.csv")

    genHash = 'generateHash=false'
    if hash_generation:
        genHash = 'generateHash=true'
    # Warning: Running droid creates a derby.log file in the CWD.

##    auskommentiert, damit droid nicht läuft
    subprocess.run([droid_call,
                    '-R', '-a', folder_input, '-At', '-Wt', '-Pr', genHash, '-p', complete_droid])
    subprocess.run([droid_call,
                    '-p', complete_droid, '-E', complete_droid_csv])

    report_info = []
    df_droid = pd.read_csv(complete_droid_csv)
    report_info.append(f'Number of analyzed files: {df_droid[df_droid['TYPE'] != 'Folder'].shape[0]}\n')
    report_info.append(f'Number of unambiguously identified files: {df_droid[df_droid['FORMAT_COUNT'] == 1].shape[0]}\n')
    report_info.append(f'Number of ambiguously identified files: {df_droid[df_droid['FORMAT_COUNT'] > 1].shape[0]}\n')
    report_info.append(f'Number of unidentified files: {df_droid[df_droid['FORMAT_COUNT'] == 0].shape[0]}\n')

    return report_info, complete_droid_csv


def sf_analyze(droid_file, output_folder):
    # Achtung: beim Einlesen werde manche Dateitypen geändert, z.B. Int zu Float(?)
    droid_complete_csv = pd.read_csv(droid_file)
    droid_complete_csv[['sf_id', 'sf_warning', 'sf_errors']] = None
    droid_sf_csv = os.path.join(output_folder, "droid_sf.csv")
    print("Siegfried analysis started.")
    for i in range(len(droid_complete_csv)):
        #for i in range(5):
        #print(droid_complete_csv['NAME'].iloc[i])
        if droid_complete_csv['TYPE'].iloc[i] == ('File' or 'Container'):
            sf_an_path = droid_complete_csv['FILE_PATH'].iloc[i]
            # print(sf_an_path)
            droid_fmt = droid_complete_csv['PUID'].iloc[i]
            droid_fmt_count = droid_complete_csv['FORMAT_COUNT'].iloc[i]
            # print(type(sf_an_path))
            # print(droid_fmt)
            # print(droid_fmt_count)
            # sf_res = subprocess.run([sf_call, '-csv', sf_an_path])

            ## auskommentiert, damit sf nicht läuft
            sf_res = subprocess.check_output([sf_call, '-csv', sf_an_path], text=True)
            csv_io = StringIO(sf_res)
            df_sf_res = pd.read_csv(csv_io)

            droid_complete_csv.loc[i, 'sf_id'] = df_sf_res['id'].iloc[0]
            droid_complete_csv.loc[i, 'sf_warning'] = df_sf_res['warning'].iloc[0]
            droid_complete_csv.loc[i, 'sf_errors'] = df_sf_res['errors'].iloc[0]



    #print(droid_complete_csv['PARENT_ID'].iloc[i])
    droid_complete_csv['PARENT_ID'] = (
        pd.to_numeric(droid_complete_csv['PARENT_ID'], errors='coerce').astype('Int64'))
    droid_complete_csv['SIZE'] = (
        pd.to_numeric(droid_complete_csv['SIZE'], errors='coerce').astype('Int64'))
    droid_complete_csv['FORMAT_COUNT'] = (
        pd.to_numeric(droid_complete_csv['FORMAT_COUNT'], errors='coerce').astype('Int64'))
    droid_complete_csv.to_csv(droid_sf_csv, index=False)

    return droid_complete_csv


def jhove_and_copy(droid_sf_analysis, output_folder, dojh, jhove_fl, jh_conf, jh_conf_f, mkcp):
    # TODO: Methoden so auseinanderbauen, dass sf- Tabelle und jhove getrennt
    if dojh:
        if jh_conf:
            df_jhove_conf = pd.read_csv(jh_conf_f)
            # print(df_jhove_conf['PUID'])
            # print(df_jhove_conf['jhove_module'])
        droid_sf_analysis[['sf_EQ_droid', 'jh_RepMod', 'jh_status', 'jh_error', 'jh_error_id']] = None
        folders = {'not_valid_dir': 'not_valid',
                   'unwell_dir': 'not_well_formed',
                   'mult_dir': 'mult_fmt_id'}
    else:
        droid_sf_analysis[['sf_EQ_droid']] = None
        folders = {'mult_dir': 'mult_fmt_id'}
    #jhove_formats = ['fmt']
    #cppath = ''
    if mkcp:
        for f in folders:
            fold_path = setup_dir(output_folder, folders[f])
            folders[f] = fold_path
    counter = 0
    for i in range(len(droid_sf_analysis)):
        counter += 1
        cppath = ''
        # Bedingungen noch verfeinern
        if droid_sf_analysis.loc[i, 'TYPE'] == ('File' or 'Container'):
            file_path = droid_sf_analysis.loc[i, 'FILE_PATH']
            if droid_sf_analysis['FORMAT_COUNT'].iloc[i] !=1  or droid_sf_analysis['sf_id'].iloc[i] != droid_sf_analysis['PUID'].iloc[i]:
                droid_sf_analysis.loc[i, 'sf_EQ_droid'] = False
                #dest_file = os.path.join(folders['mult_dir'], os.path.basename(file_path))
                if mkcp:
                    cppath = folders['mult_dir']
            else:
                droid_sf_analysis.loc[i, 'sf_EQ_droid'] = True
                # Prüfen: gibt es Fälle, wenn !=1 und trotzdem korrekt erkannt?
                # Sinnvoller: jhove auswählen lassen oder HUL festlegen?
                # oder Liste von Formaten, um Bytestream-"Prüfung" auszuschließen?
                if dojh:
                    if droid_sf_analysis.loc[i, 'FORMAT_COUNT'] == 1:
                        #                        print(droid_sf_analysis.loc[i, 'PUID'])
                        #                        print(df_jhove_conf['PUID'])
                        if jh_conf:
                            if droid_sf_analysis.loc[i, 'PUID'] in df_jhove_conf['PUID'].values:
                                puid = droid_sf_analysis.loc[i, 'PUID']
                                row = df_jhove_conf[df_jhove_conf['PUID'] == puid]
                                jhove_mod = row['jhove_module'].values[0]
                                print(jhove_mod)
                                jhove_xml = subprocess.check_output(['jhove', '-m', jhove_mod, '-h', 'xml', file_path], text=True)
                            else:
                                print('no jhove-mod')
                                jhove_xml = subprocess.check_output(['jhove', '-h', 'xml', file_path], text=True)
                        else:
                            print('no config')
                            jhove_xml = subprocess.check_output(['jhove', '-h', 'xml', file_path], text=True)
                            ## XML only saved if an error occurs
                        xml_file = os.path.join(jhove_fl, f'xml_{str(counter)}.xml')
                        with open(xml_file, 'w') as jhove_file:
                            jhove_file.write(jhove_xml)
                        jhove_tree = etree.parse(xml_file)
                        root = jhove_tree.getroot()
                        namespaces = {'jhove': 'http://schema.openpreservation.org/ois/xml/ns/jhove'}
                        status = root.xpath("//jhove:jhove/jhove:repInfo/jhove:status", namespaces=namespaces)
                        for s in status:
                            print(f'status {s.text}')
                            if s.text in ['Not well-formed', 'Well-Formed, but not valid']:
                                messages = root.xpath("//jhove:jhove/jhove:repInfo/jhove:messages", namespaces=namespaces)
                                #print(type(messages))
                                for m in messages:
                                    message_tree = m.iter(tag=etree.Element)
                                    for n in message_tree:
                                        if 'severity' in n.attrib.keys():
                                            if n.attrib['severity'] == 'error':
                                                print(f'{n.attrib['id']}')
                                                print(f'{n.text}')
                            else:
                                # TODO eigentlich wünschenswert: XML nur speichern, wenn Problem, aber: aus irgendeinem Grund
                                # will etree zwar aus dem File laden, aber nicht direkt jhove_xm
                                os.remove(xml_file)

                        # for element in root.iter(tag=etree.Element):
                        #     print(f'{element.tag} {element.text}')
                        # TODO: Auch über XML-Output regeln?
                        jhove_output = subprocess.check_output(['jhove', file_path], text=True)
                        jhove_output_array = jhove_output.split('\n')
                        bytestream = False
                        error_fd = False
                        for item in jhove_output_array:
                            #print(item)
                            if "ReportingModule: " in item:
                                mod = item.split(': ')[1].split(',')[0]
                                droid_sf_analysis.loc[i, 'jh_RepMod'] = mod
                                if mod == 'BYTESTREAM':
                                    bytestream = True
                            if "Status: " in item:
                                status = item.split(': ')[1]
                                if mkcp:
                                    if status == 'Not well-formed':
                                        cppath = folders['unwell_dir']
                                    elif status == 'Well-Formed, but not valid':
                                        cppath = folders['not_valid_dir']
                                if bytestream:
                                    status = "BS! " + status
                                droid_sf_analysis.loc[i, 'jh_status'] = status
                            if "ErrorMessage: " in item:
                                error_fd = True
                                error = item.split(': ')[1]
                                droid_sf_analysis.loc[i, 'jh_error'] = error
                            if "ID: " in item:
                                if error_fd:
                                    error_id = item.split(': ')[1]
                                    droid_sf_analysis.loc[i, 'jh_error_id'] = error_id
                        #print(cppath)
            if mkcp and cppath != '':
                # print('kopieren!')
                # print(file_path)
                # print(cppath)
                if os.path.exists(cppath):
                    shutil.copy(file_path, cppath)

    if dojh:
        dr_sf_jh_csv = os.path.join(output_folder, "droid_sf_jhove.csv")
    else:
        dr_sf_jh_csv = os.path.join(output_folder, "droid_sf_compare.csv")
    droid_sf_analysis.to_csv(dr_sf_jh_csv, index=False)

    report_info_sf = []
    report_info_sf.append(f'Number of files with different results for droid and siegfried:'
                          f' {droid_sf_analysis[droid_sf_analysis['sf_EQ_droid'] == 'False'].shape[0]}\n')
    report_info_sf.append(f'Number of files with siegfried error: '
                          f'{droid_sf_analysis[droid_sf_analysis['sf_errors'].notnull()].shape[0]}\n')
    report_info_sf.append(f'Number of files with siegfried warning: '
                          f'{droid_sf_analysis[droid_sf_analysis['sf_warning'].notnull()].shape[0]}\n')

    # report for jhove empty if no jhove analysis is done
    report_info_jh = []
    if dojh:
        jhove_status = ['Well-Formed', 'Well-Formed, but not valid', 'Well-Formed and valid',
                        'Not Well-Formed']
        bytestream_status = 'BS! Well-Formed and valid'
        for status in jhove_status:
            report_info_jh.append(f'Number of files with status {status}: '
                                  f'{droid_sf_analysis[droid_sf_analysis['jh_status'] == status].shape[0]}\n')
        report_info_jh.append(f'Number of files that could only validated with BYTESTREAM module: '
                              f'{droid_sf_analysis[droid_sf_analysis['jh_status'] == bytestream_status].shape[0]}\n')

    return report_info_sf, report_info_jh
    #print(jhove_output[rpm_id:])
    # print(droid_sf_analysis['FILE_PATH'].iloc[i])


(analyze, output, dsf_update, decompress, droiding, hash_gen, sf_ing, do_jhove, jhove_fol, prop_jhove_config,
    jhove_config_file, make_copy) = setup_config()
# print(analyze)
# print(output)
report = ["Results from analysis\n\n"]

if droiding or sf_ing or do_jhove:
    versions_for_rep = check_versions(droiding, sf_ing, do_jhove)
    report.append("Used versions of software:\n")
    for i in versions_for_rep:
        report.append(i)
    report.append('\n')
if dsf_update:
    droid_sf_update()
if decompress:
    report.append("Results from unpacking:\n")
    droid_comp = droid_compressed(analyze, output)
    unpack_rep_info = droid_decomp_routine(droid_comp, output)
    for i in unpack_rep_info:
        report.append(i)
    report.append('\n')
if droiding:
    report.append("Results from Droid:\n")
    droid_rep_info, complete_droidfile = droid_complete(analyze, output, hash_gen)
    for i in droid_rep_info:
        report.append(i)
    report.append('\n')
# print(complete_droidfile)
    if sf_ing:
        report.append("Results from Siegfried:\n")
        droid_sf = sf_analyze(complete_droidfile, output)
        sf_rep_info, jh_rep_info = jhove_and_copy(droid_sf, output, do_jhove, jhove_fol, prop_jhove_config, jhove_config_file, make_copy)
        for i in sf_rep_info:
            report.append(i)
        if do_jhove:
            report.append("\nResults from Jhove:\n")
            for i in jh_rep_info:
                report.append(i)

#print(report)

report_path = os.path.join(output, 'report.txt')
print(report)
with open(report_path, 'w') as report_txt:
    for line in report:
        report_txt.write(line)