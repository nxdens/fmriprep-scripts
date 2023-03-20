#!/bin/bash

printf "Start time: "; /bin/date
printf "Job is running on node: "; /bin/hostname
printf "Job running as user: "; /usr/bin/id
printf "Job is running in directory: "; /bin/pwd
printf "Job has proccess ID: "; $1

# this script is for run fmriprep docker to preprocess nemo data.
OUTPUT_DIR='/out'
BIDS_DIR='/public/lwang/camcan'
fs_license='/public/lwang/license.txt'
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

ls /public/lwang

#copy freesurfer license
cp $fs_license /opt/freesurfer/license.txt

mkdir $OUTPUT_DIR

fmriprep \
${BIDS_DIR} ${OUTPUT_DIR} participant \
--participant_label ${subject} \
--fs-no-reconall \
--nprocs 8

ls ${OUTPUT_DIR}

stashcp ${OUTPUT_DIR} /public/lwang/camcan/derivatives/fmriprep/${subject}