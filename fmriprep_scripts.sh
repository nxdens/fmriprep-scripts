#!/bin/bash

# this script is for run fmriprep docker to preprocess nemo data.
OUTPUT_DIR='/public/lwang/camcan/derivatives/fmriprep'
BIDS_DIR='/public/lwang/camcan'
#filename='/home/jinh2@acct.upmchs.net/hj_data/Nemo/Nemo_test/nemo_subject_list_test_7T.txt'
fs_license='/home/lwang/license.txt'
subject='sub-CC110033'

# ----- run fmripre docker ----------------
# n=1
# while read line; do
#     # reading each line
#     # echo "Line No. $n : $line"
#     IFS='/'
#     read -a strarr <<< $line
#     subject=${strarr[0]}
#     session=${strarr[1]}
#     echo "subject: $subject"
#     echo "session: $session"
#     echo "${BIDS_DIR}/sub-${subject}"

#     docker run --cpus "8" -m 16g --rm -i \
#     -v "${BIDS_DIR}:/data:ro" \
#     -v "${OUTPUT_DIR}:/out" \
#     -v "${fs_license}:/opt/freesurfer/license.txt" \
#     nipreps/fmriprep:22.0.0 \
#     /data /out/out participant \
#     --participant_label ${subject} \
#     --fs-no-reconall \
#     -w /out/work/

#     n=$((n+1))
# done < $filename


docker run --cpus "8" -m 16g --rm -i \
-v "${BIDS_DIR}:/data:ro" \
-v "${OUTPUT_DIR}:/out" \
-v "${fs_license}:/opt/freesurfer/license.txt" \
nipreps/fmriprep:22.0.0 \
/data /out/out participant \
--participant_label ${subject} \
--fs-no-reconall \
--nprocs 8 --omp-nthreads 4 \
