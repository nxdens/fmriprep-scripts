from pydeface import utils as pdu
import argparse
import os
import paramiko
from fix_check_bids import walk_dir, check_modality_folder
from make_bids import check_and_create_folder
import concurrent.futures
from tqdm import tqdm

IGNORE = "ratio_map_nyul.nii.gz"

BIDS_DTYPES = ["func", "anat", "dwi", "fmap", "beh", "meg", "eeg", "ieeg", "pet", "swi"]

DEFACE_TYPES = ["anat", "func"]

NUM_FILES = 3244

parser = argparse.ArgumentParser(description="Fix/check BIDS directory structure")
parser.add_argument("-dir", help="Top level BIDS directory", default=".", nargs="?")
parser.add_argument(
    "-remote_dir", "-rd", help="Remote directory", default=None, nargs="?"
)
parser.add_argument("-workers", "-w", help="Number of workers", default=4, nargs="?")
parser.add_argument("-dry_run", "-d", help="Dry run", action="store_true")


def is_image(path):
    return (
        os.path.isfile(path)
        and (path.endswith(".nii") or path.endswith(".nii.gz"))
        and check_modality_folder(path, modalities=DEFACE_TYPES)
        and not path.endswith(IGNORE)
    )


def get_defaced_list(project_dir):
    defaced_list = []
    for item in walk_dir(project_dir):
        if is_image(item):
            defaced_list.append(item)
    return defaced_list


def convert_path_for_deface(project_dir, path, remote_dir=None):
    file_name = os.path.basename(path)
    split_name = file_name.split("_")
    split_name.insert(-1, "desc-defaced")
    new_file_name = "_".join(split_name)

    subject_id = os.path.basename(os.path.dirname(os.path.dirname(path)))
    modality = os.path.basename(os.path.dirname(path))
    out_folder = os.path.join(
        project_dir, "derivatives", "defaced", subject_id, modality
    )
    if remote_dir:
        out_folder = os.path.join(
            remote_dir, "derivatives", "defaced", subject_id, modality
        )

    out_file = os.path.join(out_folder, new_file_name)

    return (out_folder, out_file)


def deface_image(image_path, dry_run, project_dir):
    print(image_path)

    out_path, out_file = convert_path_for_deface(project_dir, image_path)

    check_and_create_folder(out_path, dry_run)
    if not dry_run:
        pdu.deface_image(image_path, out_file)
    else:
        print("Would have defaced: {} to {}".format(image_path, out_file))


def deface_bids(project_dir, deface_list, dry_run, num_workers=4):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(deface_image(item, dry_run, project_dir))
            for item in tqdm(deface_list, total=NUM_FILES)
        ]
        concurrent.futures.wait(futures)


def sftp_upload_file(sftp, file_path, remote_dir, dry_run):
    remote_path = os.path.join(remote_dir, os.path.basename(file_path))

    try:
        sftp.stat(remote_path)
    except FileNotFoundError:
        sftp.mkdir(remote_path, parents=True)
    if not dry_run:
        sftp.put(file_path, remote_path)
    else:
        print("Would have uploaded: {} to {}".format(file_path, remote_path))


def upload_osg(project_dir, deface_list, remote_dir, dry_run, num_workers=4):
    USERNAME = "lwang"
    HOST = "login05.osgconnect.net"
    SSH_KEY_PATH = "/home/lwang/.ssh/id_rsa"

    defaced_list = [
        (
            convert_path_for_deface(project_dir, image_path)[0],
            convert_path_for_deface(project_dir, image_path, remote_dir=remote_dir)[0],
        )
        for image_path in deface_list
    ]

    print(defaced_list)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USERNAME, key_filename=SSH_KEY_PATH)

    sftp = ssh.open_sftp()
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        sftp.mkdir(remote_dir, parents=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for (local_file_path, remote_file_paths) in defaced_list:
            futures.append(
                executor.submit(
                    sftp_upload_file, local_file_path, remote_file_paths, dry_run
                )
            )


def make_derivatives_folder(project_dir, dry_run):
    derivatives_folder = os.path.join(project_dir, "derivatives")
    check_and_create_folder(derivatives_folder, dry_run)


def main():
    args = parser.parse_args()
    deface_list = get_defaced_list(args.dir)
    deface_bids(args.dir, deface_list, args.dry_run, num_workers=args.workers)
    if args.remote_dir:
        upload_osg(args.dir, deface_list, args.remote_dir, args.dry_run, args.workers)


if __name__ == "__main__":
    main()
