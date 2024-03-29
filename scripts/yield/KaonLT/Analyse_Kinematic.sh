#!/bin/bash
# 23/07/21 - Stephen Kay, University of Regina
# Script to analyse an entire kaon kinematic setting
# !!! 31/08/21 !!!
# !!! WARNING !!!
# This needs updating, Junaid removed some of the old scripts and created new versions
# This script will need to be tweaked to run the newer scripts instead of the old ones 
# !!! WARNING !!!
# !!! 31/08/21 !!!

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

# Set path depending upon hostname. Change or add more as needed  
if [[ "${HOSTNAME}" = *"farm"* ]]; then  
    REPLAYPATH="/group/c-kaonlt/online_analysis/hallc_replay_lt"
    if [[ "${HOSTNAME}" != *"ifarm"* ]]; then
	source /site/12gev_phys/softenv.sh 2.3
	source /apps/root/6.18.04/setroot_CUE.bash
    fi
    cd "$REPLAYPATH"
    source "$REPLAYPATH/setup.sh"
elif [[ "${HOSTNAME}" = *"qcd"* ]]; then
    REPLAYPATH="/group/c-kaonlt/USERS/${USER}/hallc_replay_lt"
    source /site/12gev_phys/softenv.sh 2.3
    source /apps/root/6.18.04/setroot_CUE.bash
    cd "$REPLAYPATH"
    source "$REPLAYPATH/setup.sh" 
elif [[ "${HOSTNAME}" = *"cdaq"* ]]; then
    REPLAYPATH="/home/cdaq/hallc-online/hallc_replay_lt"
elif [[ "${HOSTNAME}" = *"phys.uregina.ca"* ]]; then
    REPLAYPATH="/home/${USER}/work/JLab/hallc_replay_lt"
fi
UTILPATH="${REPLAYPATH}/UTIL_KAON"
RunListFile="${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}"
if [ ! -f "${RunListFile}" ]; then
    echo "Error, ${RunListFile} not found, exiting"
    exit 3
fi
cd $REPLAYPATH

if [ -f "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses" ]; then
    rm "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
else touch "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
fi

TestingVar=$((1))
while IFS='' read -r line || [[ -n "$line" ]]; do
    runNum=$line
    if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root" ]; then
	echo "Analysis not found for run $runNum in ${UTILPATH}/scripts/yield/KaonLT/OUTPUT/"
	echo "${runNum}" >> "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
	TestingVar=$((TestingVar+1))
    fi
done < "$RunListFile"

if [ $TestingVar == 1 ]; then
    echo "All KaonLT  analysis files found"
    rm "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
elif [ $TestingVar != 1 ]; then
    cp "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses" "$REPLAYPATH/UTIL_BATCH/InputRunLists/${KINEMATIC}_MissingAnalyses"
    if [ $Autosub == 1 ]; then
	while IFS='' read -r line || [[ -n "$line" ]]; do
	    runNum=$line
	    if [ -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root" ]; then
		rm "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root"
	    fi
	    if [ -f "${UTILPATH}/ROOTfiles/Analysis/KaonLT/Kaon_coin_replay_production_${runNum}_-1.root" ]; then
		rm "${UTILPATH}/ROOTfiles/Analysis/KaonLT/Kaon_coin_replay_production_${runNum}_-1.root"
	    fi
	done < "${UTILPATH}/scripts/yield/KaonLT/Kinematics/${KINEMATIC}_MissingAnalyses"
	yes y | eval "$REPLAYPATH/UTIL_BATCH/batch_scripts/run_batch_KaonLT.sh ${KINEMATIC}_MissingAnalyses"
    elif [ $Autosub != 1 ]; then
	echo "Analyses missing, list copied to UTIL_BATCH directory, run on farm if desired"
	read -p "Process python script for missing replays/analyses interactively? <Y/N> " prompt2
	if [[ $prompt2 == "y" || $prompt2 == "Y" || $prompt2 == "yes" || $prompt2 == "Yes" ]]; then
	    while IFS='' read -r line || [[ -n "$line" ]]; do
		runNum=$line
		if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${runNum}_-1_Analysed_Data.root" ]; then
		    python3 $UTILPATH/scripts/yield/KaonLT/src/Kaonyield.py "Kaon_coin_replay_production" ${runNum} "-1"
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
	    hadd ${KINFILE} ${RootName}
	else echo "Not removing and remaking, will attempt to proces existing file"
	fi
    fi
    if [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaons.root" ]; then
	root -b -l -q "${UTILPATH}/scripts/yield/KaonLT/PlotKaonPhysics.C(\"${KINFILE}\", \"${KINEMATIC}_Kaons\")"
    elif [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaons.pdf" ]; then
	root -b -l -q "${UTILPATH}/scripts/yield/KaonLT/PlotKaonPhysics.C(\"${KINFILE}\", \"${KINEMATIC}_Kaons\")"
    else echo "Kaon plots already found in - ${UTILPATH}/OUTPUT/Analysis/KaonLT/${KINEMATIC}_Kaons.root and .pdf - Plotting macro skipped"
    fi
fi

exit 0

