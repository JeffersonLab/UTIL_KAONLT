#!/bin/bash
# 23/07/21 - Stephen Kay, University of Regina
# Script to analyse an entire kaon kinematic setting
# 03/02/22 - SJDK - Modified script to use newest versions of plotting and analysis scripts as appropriate
# I also modified the script to get the target type from the kin file name where it's relevant, it will default to LH2 otherwise

KINEMATIC=$1

if [[ -z "$1" ]]; then
    echo "I need a kinematic setting to process!"
    echo "Please provide a kinematic setting as input"
    exit 2
fi
declare -i Autosub=0
read -p "Auto submit batch jobs for missing replays/analyses? <Y/N> " prompt
if [[ $prompt == "y" || $prompt == "Y" || $prompt == "yes" || $prompt == "Yes" ]]; then
    Autosub=$((Autosub+1))
else echo "Will not submit any batch jobs, please check input lists manually and submit if needed"
fi

echo "######################################################"
echo "### Processing kinematic ${KINEMATIC} ###"
echo "######################################################"

# Runs script in the ltsep python package that grabs current path enviroment
if [[ ${HOSTNAME} = *"cdaq"* ]]; then
    PATHFILE_INFO=`python3 /home/cdaq/kaonLT-2021/hallc_replay_lt/UTIL_KAON/bin/python/ltsep/scripts/getPathDict.py $PWD` # The output of this python script is just a comma separated string
elif [[ "${HOSTNAME}" = *"farm"* ]]; then
    PATHFILE_INFO=`python3 /u/home/${USER}/.local/lib/python3.4/site-packages/ltsep/scripts/getPathDict.py $PWD` # The output of this python script is just a comma separated string
fi

# Split the string we get to individual variables, easier for printing and use later
VOLATILEPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f1` # Cut the string on , delimitter, select field (f) 1, set variable to output of command
ANALYSISPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f2`
HCANAPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f3`
REPLAYPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f4`
UTILPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f5`
PACKAGEPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f6`
OUTPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f7`
ROOTPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f8`
REPORTPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f9`
CUTPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f10`
PARAMPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f11`
SCRIPTPATH=`echo ${PATHFILE_INFO} | cut -d ','  -f12`
ANATYPE=`echo ${PATHFILE_INFO} | cut -d ','  -f13`
USER=`echo ${PATHFILE_INFO} | cut -d ','  -f14`
HOST=`echo ${PATHFILE_INFO} | cut -d ','  -f15`

RunListFile="${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}"
if [ ! -f "${RunListFile}" ]; then
    echo "Error, ${RunListFile} not found, exiting"
    exit 3
fi
cd $REPLAYPATH

# 03/02/22 - SJDK - Determine target type from kin file name, default to LH2 if not in name
if [[ ${KINEMATIC} == *"_LH"* ]]; then
    TargetType="LH2"
elif [[ ${KINEMATIC} == *"_LD"* ]]; then
    TargetType="LD2"
else TargetType="LH2"
fi

if [ -f "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses" ]; then
    rm "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
else touch "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses" && chmod 775 "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
fi

TestingVar=$((1))
while IFS='' read -r line || [[ -n "$line" ]]; do
    runNum=$line
    if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root" ]; then
	echo "Analysis not found for run $runNum in ${UTILPATH}/OUTPUT/"
	echo "${runNum}" >> "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
	TestingVar=$((TestingVar+1))
    fi
done < "$RunListFile"

# 03/02/22 - SJDK - Script calls v3 for python scripts, these versions need the target type specified (they default to LH2)
if [ $TestingVar == 1 ]; then
    echo "All KaonLT  analysis files found"
    rm "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
elif [ $TestingVar != 1 ]; then
    cp "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses" "$REPLAYPATH/UTIL_BATCH/InputRunLists/Kaon_Data/${KINEMATIC}_MissingAnalyses"
    chmod 775 "$REPLAYPATH/UTIL_BATCH/InputRunLists/Kaon_Data/${KINEMATIC}_MissingAnalyses"
    if [ $Autosub == 1 ]; then
	while IFS='' read -r line || [[ -n "$line" ]]; do
	    runNum=$line
	    if [ -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root" ]; then
		rm "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root"
	    fi
	    if [ -f "${UTILPATH}/ROOTfiles/Analysis/KaonLT/Kaon_coin_replay_production_${runNum}_-1.root" ]; then
		rm "${UTILPATH}/ROOTfiles/Analysis/KaonLT/Kaon_coin_replay_production_${runNum}_-1.root"
	    fi
	done < "${UTILPATH}/scripts/online_physics/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
	# 03/02/22 - SJDK - This script needs to be checked, may not run v3 scripts (which require a target type too)
	yes y | eval "$REPLAYPATH/UTIL_BATCH/batch_scripts/run_batch_KaonLT.sh Kaon_Data/${KINEMATIC}_MissingAnalyses" # SJDK 11/01/22 - Need to check this script is actually OK tbh...
	sleep 2
	rm "$REPLAYPATH/UTIL_BATCH/InputRunLists/Kaon_Data/${KINEMATIC}_MissingAnalyses" 
    elif [ $Autosub != 1 ]; then
	echo "Analyses missing, list copied to UTIL_BATCH directory, run on farm if desired"
	read -p "Process python script for missing replays/analyses interactively? <Y/N> " prompt2
	if [[ $prompt2 == "y" || $prompt2 == "Y" || $prompt2 == "yes" || $prompt2 == "Yes" ]]; then
	    while IFS='' read -r line || [[ -n "$line" ]]; do
		runNum=$line
		if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root" ]; then
		    python3 $UTILPATH/scripts/online_physics/KaonLT/kaon_prod_analysis_sw_v3.py "Kaon_coin_replay_production" ${runNum} "-1" ${TargetType}
		fi
            done < "$RunListFile"
	else echo "Not processing python script interactively"
	fi
    fi
fi

if [ $TestingVar == 1 ]; then
    while IFS='' read -r line || [[ -n "$line" ]]; do
	runNum=$line
	RootName+="${runNum}_-1_Analysed_Data.root "
    done < "$RunListFile"
    cd "${UTILPATH}/OUTPUT/Analysis/KaonLT/"
    KINFILE="${KINEMATIC}_Analysed_Data.root"
    if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINFILE}" ]; then
	hadd ${KINFILE} ${RootName}
    elif [ -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINFILE}" ]; then
	read -p "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINFILE} already found, remove and remake? <Y/N> " prompt3 
	if [[ $prompt3 == "y" || $prompt3 == "Y" || $prompt3 == "yes" || $prompt3 == "Yes" ]]; then
	    rm "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINFILE}"
	    hadd ${KINFILE} ${RootName} # This step combines all of the analysed data into a single rootfile, which we then process with the plotting script
	else echo "Not removing and remaking, will attempt to proces existing file"
	fi
    fi
    if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaon_Analysis_Distributions.pdf" ]; then
	python3 ${UTILPATH}/scripts/online_physics/KaonLT/PlotKaonPhysics_sw.py -1 ${runNum} -1 ${TargetType} ${KINFILE}
    elif [ -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaon_Analysis_Distributions.pdf" ]; then
	    read -p "Kaon analysis plots already found in - ${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaon_Analysis_Distributions.pdf, remove and remake? <Y/N> " prompt4
	    if [[ $prompt4 == "y" || $prompt4 == "Y" || $prompt4 == "yes" || $prompt4 == "Yes" ]]; then
		 rm "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaon_Analysis_Distributions.pdf"
		 python3 ${UTILPATH}/scripts/online_physics/KaonLT/PlotKaonPhysics_sw.py -1 ${runNum} -1 ${TargetType} ${KINFILE}
	    fi
	    else echo "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaon_Analysis_Distributions.pdf not removed"
    fi
fi

exit 0

