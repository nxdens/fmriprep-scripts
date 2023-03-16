import os
import shutil
import argparse
import re

BIDS_DTYPES = ['func','anat','dwi','fmap','beh','meg','eeg','ieeg','pet','swi']

DEBUG_PARAMS = {"source": "/home/wangl15@acct.upmchs.net/camcan_data", 
                "dest": "./bids_test", 
                "project": "bids_folder", 
                "subject_regex": "sub-CC[0-9]{6}"}

parser = argparse.ArgumentParser(prog='make_bids.py', description='Make BIDS directory structure')
parser.add_argument('-d', '--debug', help='Debug mode', )
parser.add_argument('-source', '-s', help='Source directory', default='.', nargs='?')
parser.add_argument('-dest', '-dt', help='Destination directory', default='.', nargs='?')
parser.add_argument('-project', '-p', help='Project name', default='bids_folder', nargs='?')
parser.add_argument('-subject_regex', '-rx', help='Regex pattern to find subject ID strings', default='*', nargs='?')
parser.add_argument('-dry_run', help='Dry run', action='store_true')


def check_and_create_folder(folder_path, dry_run):
    if not os.path.isdir(folder_path):
        if not dry_run:
            os.makedirs(folder_path)
        else:
            print("Would have created directory: {}".format(folder_path))
    else:
        if dry_run:
            print("Directory already exists: {}".format(folder_path))

def is_ID(string,subject_regex):
    if re.search(subject_regex,string):
        return True
    else:
        return False

def is_modality(string):
    if string in BIDS_DTYPES:
        return True
    else:
        return False

def make_bids_folders(source_folder,dest_folder,project_name,subject_regex,dry_run):
    project_path = os.path.join(dest_folder,project_name)
    
    check_and_create_folder(dest_folder, dry_run)
    check_and_create_folder(project_path, dry_run)
    check_and_create_folder(os.path.join(project_path,"derivatives"), dry_run)
    
    Folder_mappings = {}
    
    print(source_folder)
    for root, sub_folder, files in os.walk(source_folder):
        for folder_name in sub_folder:  
            potential_id = root.split("/")[-1]
            if is_modality(folder_name) and is_ID(potential_id,subject_regex):
                
                #remove extra folder 
                if os.path.isdir(os.path.join(root,folder_name,folder_name)):
                    os.rmdir(os.path.join(root,folder_name,folder_name))
                    
                subject_folder = os.path.join(project_path,potential_id)
                subject_modality_folder = os.path.join(subject_folder,folder_name)
                
                check_and_create_folder(subject_folder, dry_run)
                check_and_create_folder(subject_modality_folder, dry_run)
                
                original_path = os.path.join(root,folder_name)
                
                if Folder_mappings.get(original_path) is None:
                    Folder_mappings[original_path] = [subject_modality_folder]
                else:
                    Folder_mappings[original_path].append(subject_modality_folder)
                
    return Folder_mappings
            
def check_and_move(source_folder,dest_folder,dry_run):
    #check subject_id and modality
    if not dry_run:
        shutil.move(source_folder, dest_folder)
    else:
        print("Would have moved folder: {} to {}".format(source_folder, dest_folder))
        
        
def move_folders(mapping,dry_run):
    for source_folder in mapping:
        for dest_folder in mapping[source_folder]:
            check_and_move(source_folder,dest_folder, dry_run)
    
def main():
    args = parser.parse_args()
    
    if args.debug:
        args.source = DEBUG_PARAMS["source"]
        args.dest = DEBUG_PARAMS["dest"]
        args.project = DEBUG_PARAMS["project"]
        args.subject_regex = DEBUG_PARAMS["subject_regex"]
        args.dry_run = True
    
    print(args)
    source_folder = args.source
    dest_folder = args.dest
    project_name = args.project
    dry_run = args.dry_run
    subject_regex = args.subject_regex
    
    source_to_dest_mapping = make_bids_folders(source_folder,
                                               dest_folder,
                                               project_name,
                                               subject_regex,
                                               dry_run)
    print("source_to_dest_mapping: {}".format(source_to_dest_mapping))
    print("moving folders")
    move_folders(source_to_dest_mapping, dry_run)
    
if __name__ == "__main__":
    main()