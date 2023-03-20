import paramiko
import os
import re
import argparse
from fix_check_bids import walk_dir, check_modality_folder
from make_bids import check_and_create_folder

IGNORE = "ratio_map_nyul.nii.gz"

BIDS_DTYPES = ["func", "anat", "dwi", "fmap", "beh", "meg", "eeg", "ieeg", "pet", "swi"]

DEFACE_TYPES = ["anat", "func"]

NUM_FILES = 3244

parser = argparse.ArgumentParser(description="Fix/check BIDS directory structure")
parser.add_argument("-dir", help="Top level BIDS directory", default=".", nargs="?")
parser.add_argument(
    "-remote_dir", "-rd", help="Remote directory", default=None, nargs="?"
)
parser.add_argument("-dry_run", "-d", help="Dry run", action="store_true")


def try_make_remote_dir(sftp, remote_dir, dry_run):
    try:
        sftp.stat(remote_dir)
    except:
        if not dry_run:
            sftp.mkdir(remote_dir)
        else:
            print("Would have made directory: {}".format(remote_dir))


def upload_osg(project_dir, remote_dir, dry_run):
    USERNAME = "lwang"
    HOST = "login05.osgconnect.net"
    SSH_KEY_PATH = "/home/wangl15@acct.upmchs.net/.ssh/id_osg"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USERNAME, key_filename=SSH_KEY_PATH)
    sftp = ssh.open_sftp()

    try:
        sftp.put("./fmriprep_scripts.sh", "/home/lwang/fmriprep_scripts.sh")
    except:
        print("File already exists")

    try:
        sftp.put("./camcan_fmriprep.submit", "/home/lwang/camcan_fmriprep.submit")
    except:
        print("File already exists")

    try_make_remote_dir(sftp, remote_dir, dry_run)
    try_make_remote_dir(sftp, os.path.join(remote_dir, "derivatives"), dry_run)
    try_make_remote_dir(
        sftp, os.path.join(remote_dir, "derivatives", "fmriprep"), dry_run
    )
    subject_list = []

    for root, dirs, files in os.walk(project_dir):
        for name in dirs:
            if re.match(r"sub-CC\d{6}", name):
                remote_file_path = os.path.join(
                    remote_dir, "derivatives", "fmriprep", name
                )
                subject_list.append(name)
                print(name)
                # try_make_remote_dir(sftp, remote_file_path, dry_run)

    sftp.close()
    ssh.close()


def main():
    args = parser.parse_args()
    upload_osg(args.dir, args.remote_dir, args.dry_run)


if __name__ == "__main__":
    main()
