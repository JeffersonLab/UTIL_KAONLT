#! /bin/bash
###########################################################################################################################
# Created - 20/July/21, Author - Muhammad Junaid (mjo147@uregina.ca), University of Regina, Canada (Copyright (c) junaid) #
# 28/11/21 - Version 2 - Utilises new ltsep package by Richard Trotta
# 19/01/22 - Version 3 - Target type is now an argument
###########################################################################################################################
# This version of script is for shift workers at JLAB
# Executes the replay script and python analysis script and at the end python plotting script
# To run this script, execute ./scriptname $RUNNUMBER$

#################################################################################################################################################

echo "Starting analysis of Kaon events"
echo "I take as arguments the run number and max number of events!"
# Input params - run number and max number of events
RUNNUMBER=$1
if [[ -z "$1" ]]; then
    echo "I need an input run number"
    echo "Please provide a run number as input"
fi
TARGET=$2
if [[ -z "$2" ]]; then
    echo "I need a Target type"
    echo "Please provide a Target (LH2, LD2 or Dummy10cm)"
fi
MAXEVENTS=$3
if [[ -z "$3" ]]; then
    echo "Only Run Number entered...I'll assume -1 (all) events!" 
    MAXEVENTS=-1
fi

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

# #################################################################################################################################################

# Source stuff depending upon hostname. Change or add more as needed  
if [[ "${HOST}" = *"farm"* ]]; then
    if [[ "${HOST}" != *"ifarm"* ]]; then
	source /site/12gev_phys/softenv.sh 2.3
	source /apps/root/6.18.04/setroot_CUE.bash
    fi
    cd "$HCANAPATH"
    source "$HCANAPATH/setup.sh"
    cd "$REPLAYPATH"
    source "$REPLAYPATH/setup.sh"
elif [[ "${HOST}" = *"qcd"* ]]; then
    source "$REPLAYPATH/setup.sh" 
fi

cd $REPLAYPATH

# ###################################################################################################################################################
###################################################################################################################################################
# if [ ! -f "$UTILPATH/ROOTfiles/Scalers/coin_replay_scalers_${RUNNUMBER}_${MAXEVENTS}.root" ]; then
#     eval "$REPLAYPATH/hcana -l -q -b \"SCRIPTS/COIN/SCALERS/replay_coin_scalers.C($RUNNUMBER,${MAXEVENTS})\""
#     cd "$REPLAYPATH/CALIBRATION/bcm_current_map"
#     root -b -l<<EOF 
# .L ScalerCalib.C
# .x run.C("${UTILPATH}/ROOTfiles/Scalers/coin_replay_scalers_${RUNNUMBER}_${MAXEVENTS}.root")
# .q  
# EOF
#     mv bcmcurrent_${RUNNUMBER}_.param $REPLAYPATH/PARAM/HMS/BCM/CALIB/bcmcurrent_$RUNNUMBER.param
#     cd $REPLAYPATH
# else echo "Scaler replayfile already found for this run in $REPLAYPATH/ROOTfiles/Scalers - Skipping scaler replay step"
# fi

sleep 3

if [ ! -f "$UTILPATH/ROOTfiles/Analysis/KaonLT/${ANATYPE}_replay_luminosity_${RUNNUMBER}_${MAXEVENTS}.root" ]; then
    if [[ "${HOSTNAME}" != *"ifarm"* ]]; then
	if [[ "${HOSTNAME}" == *"cdaq"* ]]; then
	    eval "$REPLAYPATH/hcana -l -q -b \"SCRIPTS/COIN/PRODUCTION/FullReplay_KaonLT_Phys_Prod.C($RUNNUMBER,$MAXEVENTS)\""| tee $UTILPATH/REPORT_OUTPUT/Analysis/KaonLT/${ANATYPE}_output_coin_production_Summary_${RUNNUMBER}_${MAXEVENTS}.report
	else	
	    eval "$REPLAYPATH/hcana -l -q -b \"SCRIPTS/COIN/PRODUCTION/FullReplay_KaonLT_Phys_Prod.C($RUNNUMBER,$MAXEVENTS)\"" 
	fi
    elif [[ "${HOSTNAME}" == *"ifarm"* ]]; then
	eval "$REPLAYPATH/hcana -l -q -b \"SCRIPTS/COIN/PRODUCTION/FullReplay_KaonLT_Phys_Prod.C($RUNNUMBER,$MAXEVENTS)\""| tee $UTILPATH/REPORT_OUTPUT/Analysis/KaonLT/${ANATYPE}_output_coin_production_Summary_${RUNNUMBER}_${MAXEVENTS}.report
    fi
else echo "Replayfile already found for this run in $UTILPATH/ROOTfiles/Analysis/KaonLT/ - Skipping replay step"
fi

# sleep 3

################################################################################################################################                                                                                   
# Section for kaon analysis script
# if [ -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_Analysed_Data.root" ]; then
#     read -p "Kaon production analysis file already exists, do you want to reprocess it? <Y/N> " option1
#     if [[ $option1 == "y" || $option1 == "Y" || $option1 == "yes" || $option1 == "Yes" ]]; then
# 	rm "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_Analysed_Data.root"
# 	echo "Reprocessing"
# 	python3 ${UTILPATH}/scripts/online_physics/KaonLT/kaon_prod_analysis_sw.py Kaon_coin_replay_production ${RUNNUMBER} ${MAXEVENTS} ${TARGET}
#     else
# 	echo "Skipping python analysis script step"
#     fi
# elif [ ! -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_Analysed_Data.root" ]; then
# 	python3 ${UTILPATH}/scripts/online_physics/KaonLT/kaon_prod_analysis_sw.py Kaon_coin_replay_production ${RUNNUMBER} ${MAXEVENTS} ${TARGET}
# fi
# 
# sleep 3
# 
# ##################################################################################################################################
# # Section for kaon physics ploting script
# if [ -f "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_Output_Data.root" ]; then
#     read -p "Kaon physics plots already exits, do you want to reprocess them? <Y/N> " option2
#     if [[ $option2 == "y" || $option2 == "Y" || $option2 == "yes" || $option2 == "Yes" ]]; then
# 	rm "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_Output_Data.root"
# 	echo "Reprocessing"
# 	python3 ${UTILPATH}/scripts/online_physics/KaonLT/PlotKaonPhysics_sw.py Analysed_Data ${RUNNUMBER} ${MAXEVENTS} ${TARGET}
#     else
# 	echo "Skipping python physics plotting script step"
#     fi
# elif [ ! -f  "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_Output_Data.root" ]; then
# 	python3 ${UTILPATH}/scripts/online_physics/KaonLT/PlotKaonPhysics_sw.py Analysed_Data ${RUNNUMBER} ${MAXEVENTS} ${TARGET}
# fi
# evince "${UTILPATH}/OUTPUT/Analysis/KaonLT/${RUNNUMBER}_${MAXEVENTS}_sw_Kaon_Analysis_Distributions.pdf" &
# exit 0
