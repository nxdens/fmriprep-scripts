import os
import json
import shutil
import argparse
import bids_validator
import nibabel as nib
from copy import deepcopy
from tqdm import tqdm

BIDS_DTYPES = ["func", "anat", "dwi", "fmap", "beh", "meg", "eeg", "ieeg", "pet", "swi"]

DEBUG_PARAMS = {
    "source": "/home/wangl15@acct.upmchs.net/camcan_data",
    "dest": "./bids_test",
    "project": "bids_folder",
    "subject_regex": "sub-CC[0-9]{6}",
}
PHASE_ENCODING_REMAPPING = {
    "x": "i",
    "x-": "i-",
    "y": "j",
    "y-": "j-",
    "z": "k",
    "z-": "k-",
}

NUM_FILES = 20737

parser = argparse.ArgumentParser(description="Fix/check BIDS directory structure")
parser.add_argument(
    "-d",
    "--debug",
    help="Debug mode",
)
parser.add_argument("-dir", help="Top level BIDS directory", default=".", nargs="?")
parser.add_argument("-dry_run", "-dry", help="Dry run", action="store_true")


def walk_dir(top_dir):
    for root, dirs, files in os.walk(top_dir):
        for name in files:
            yield os.path.join(root, name)
        for name in dirs:
            yield os.path.join(root, name)


def check_modality_folder(file_path, modalities=None):
    folder_path = os.path.dirname(file_path)
    if os.path.isdir(folder_path):

        if modalities:
            comparison = modalities
        else:
            comparison = BIDS_DTYPES

        return os.path.basename(folder_path) in comparison
    else:
        return False


def check_file_error_conditions(project_dir, dry_run):
    """
    Checks for errors in BIDS directory structure. Currently only checks for phase encoding direction.
    """
    for item in (pbar := tqdm(walk_dir(project_dir), total=NUM_FILES)):
        # pbar.set_description("Checking file: {}".format(item))
        if os.path.isfile(item):
            rename_fmap(item, dry_run)
        if os.path.isfile(item) and item.endswith(".json"):
            fix_json(item, dry_run)
        if os.path.isfile(item) and (item.endswith(".nii.gz") or item.endswith(".nii")):
            fix_nifti(item, dry_run)


def fix_json(file_path, dry_run):
    """
    Fixes json files in BIDS directory structure. Currently only fixes phase encoding direction to meet BIDS spec.
    """
    if check_modality_folder(file_path, ["func"]):
        with open(file_path, "r") as f:
            original_data = json.load(f)
        data = deepcopy(original_data)
        if data["PhaseEncodingDirection"] in PHASE_ENCODING_REMAPPING.keys():
            data["PhaseEncodingDirection"] = PHASE_ENCODING_REMAPPING[
                data["PhaseEncodingDirection"]
            ]
            if dry_run:
                print("Would have fixed file: {}".format(file_path))
                print(original_data)
                print("-------------------------------------")
                print(data)
                print("=====================================")
            else:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=4)
        else:
            print("Skipping file: {}".format(file_path))


def fix_nifti(nifti_path, dry_run):
    """Fixes nifti files in BIDS directory structure. Currently only fixes TR to meet BIDS spec. TR is taken from json header."""
    if check_modality_folder(nifti_path, ["func"]):
        nib_img = nib.load(nifti_path)
        json_path = nifti_path.replace(".nii.gz", ".json").replace(".nii", ".json")
        with open(json_path, "r") as f:
            json_header = json.load(f)
        print("Using tr from json header: {}".format(json_path))
        print(json_header)

        zooms = nib_img.header.get_zooms()
        print(zooms)
        if abs(json_header["RepetitionTime"] - zooms[3]) > 0.001:
            nib_img.header.set_zooms(
                (
                    zooms[0],
                    zooms[1],
                    zooms[2],
                    json_header["RepetitionTime"],
                )
            )

            if dry_run:
                print(nib_img.header)
            else:
                nib.save(nib_img, nifti_path)
        else:
            print("No need to fix TR for file: {}".format(nifti_path))


def rename_fmap(file_path, dry_run):
    if check_modality_folder(file_path, ["fmap"]):
        file_name = os.path.basename(file_path)
        split_name = file_name.split("_")
        for index, split_marked in enumerate(split_name):
            if split_marked.startswith("epi"):
                split_name[index] = split_marked.replace("epi", "task")

        new_file_name = "_".join(split_name)
        new_path = os.path.join(os.path.dirname(file_path), new_file_name)
        if dry_run:
            print("Would have renamed file: {}".format(file_path))
            print("To: {}".format(new_path))
        else:
            os.rename(file_path, new_path)


def main():
    args = parser.parse_args()
    check_file_error_conditions(args.dir, args.dry_run)
    print(
        bids_validator.BIDSValidator().is_bids(
            "/home/wangl15@acct.upmchs.net/fmriprep-scripts/bids_test/camcan_bids_redo/sub-CC721707/anat/sub-CC721707_T1w.nii"
        )
    )


if __name__ == "__main__":
    main()
