#! /usr/bin/python
#
# Description: Grabs lumi data from corresponding csv depending on run setting. Then plots the yields and creates a comprehensive table.
# Variables calculated: current, rate_HMS, rate_SHMS, sent_edtm_PS, uncern_HMS_evts_scaler, uncern_SHMS_evts_scaler, uncern_HMS_evts_notrack, uncern_SHMS_evts_notrack, uncern_HMS_evts_track, uncern_SHMS_evts_track
# ================================================================
# Time-stamp: "2022-10-27 17:58:34 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from csv import DictReader
import sys, os, subprocess

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''

# Import package for cuts
from ltsep import Root

lt=Root(os.path.realpath(__file__))

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
SCRIPTPATH=lt.SCRIPTPATH
ANATYPE=lt.ANATYPE

################################################################################################################################################
'''
Grab proper lumi data file based of input given then define input and output file names as well as the target
'''

inp_name = sys.argv[1]

sys.path.insert(0,"%s/luminosity/src/%sLT" % (SCRIPTPATH,ANATYPE))
import data_path

data_path = data_path.get_file(inp_name,SCRIPTPATH)
target = data_path[0]
inp_f = data_path[1]
out_f = data_path[2]

################################################################################################################################################

print("\nRunning as %s on %s, hallc_replay_lt path assumed as %s" % (USER, HOST, REPLAYPATH))

# Converts csv data to dataframe
try:
    lumi_data = pd.read_csv(inp_f)
    print(inp_f)
    print(lumi_data.keys())
except IOError:
    print("Error: %s does not appear to exist." % inp_f)
    sys.exit(0)

################################################################################################################################################

# Remove runs that have zero beam on time to avoid error
lumi_data = lumi_data[lumi_data["time"] > 0.0].reset_index(drop=True)

def removeRun(runNum):
    '''
    Removes runs from DF and subsequently will not be plotted or included in yield csv output
    '''
    global lumi_data
    lumi_data = lumi_data[lumi_data["run number"] != runNum].reset_index(drop=True)
    return lumi_data

# Remove runs, removeRun(runNumber)
#removeRun(5154)

################################################################################################################################################

# Convert to dict for proper formatting when eventually merging dictionaries
lumi_data = dict(lumi_data)

################################################################################################################################################
'''
Define prescale variables
'''

# Define prescale variables
if "PS1" in lumi_data.keys() and not lumi_data["PS1"].isnull().values.any():
    SHMS_PS = lumi_data["PS1"]
    print("PS1 : ",lumi_data["PS1"])
if "PS2" in lumi_data.keys() and not lumi_data["PS2"].isnull().values.any():
    SHMS_PS = lumi_data["PS2"]
    print("PS2 : ",lumi_data["PS2"])
if "PS3" in lumi_data.keys() and not lumi_data["PS3"].isnull().values.any():
    HMS_PS = lumi_data["PS3"]
    print("PS3 : ",lumi_data["PS3"])
if "PS4" in lumi_data.keys() and not lumi_data["PS4"].isnull().values.any():
    HMS_PS = lumi_data["PS4"]
    print("PS4 : ",lumi_data["PS4"])
if "PS5" in lumi_data.keys() and not lumi_data["PS5"].isnull().values.any():
    COIN_PS = lumi_data["PS5"]
    print("PS5 : ",lumi_data["PS5"])
if "PS6" in lumi_data.keys() and not lumi_data["PS6"].isnull().values.any():
    COIN_PS = lumi_data["PS6"]
    print("PS6 : ",lumi_data["PS6"])

try:
    SHMS_PS
    HMS_PS
    COIN_PS
except NameError:
    SHMS_PS = None
    HMS_PS = None
    COIN_PS = None

################################################################################################################################################

# Define number of runs to analyze
numRuns = len(lumi_data["run number"])

def makeList(lumi_input):
    '''
    Takes input list and converts to numpy (with NaN converted to zeros) so it can be used mathematically
    '''
    new_lst = [lumi_data[lumi_input][i] for i,evts in enumerate(lumi_data["run number"])]
    new_lst = np.asarray(pd.Series(new_lst).fillna(0)) # changes NaN to zeros and convert to numpy
    return new_lst

################################################################################################################################################

def calc_yield():
    '''
    Creates a new dictionary with yield calculations. The relative yield is defined relative to the maximum current.
    '''

    # Create dictionary for calculations that were not calculated in previous scripts.
    yield_dict = {
        "current" : makeList("charge")/makeList("time"),
                        
        #"sent_edtm_PS" : makeList("sent_edtm")/HMS_PS,
        #"PS_mod" : SHMS_PS%HMS_PS,

        #"CPULT_phys" : (makeList("HMSTRIG_cut")*HMS_PS+makeList("SHMSTRIG_cut")*SHMS_PS)*makeList("CPULT_scaler"),
        "CPULT_phys" : makeList("CPULT_scaler"),

        "uncern_CPULT_phys" : makeList("CPULT_scaler_uncern"),
            
        }

    if SHMS_PS != None and HMS_PS != None:
        yield_dict.update({"sent_edtm_PS" : makeList("sent_edtm")/HMS_PS+makeList("sent_edtm")/SHMS_PS+makeList("sent_edtm")/COIN_PS+makeList("sent_edtm")/(SHMS_PS*HMS_PS*COIN_PS)-makeList("sent_edtm")/(HMS_PS*SHMS_PS)-makeList("sent_edtm")/(COIN_PS*SHMS_PS)-makeList("sent_edtm")/(HMS_PS*COIN_PS)})
        # Total livetime calculation
        TLT = makeList("accp_edtm")/yield_dict["sent_edtm_PS"]
        yield_dict.update({"TLT" : TLT})
        uncern_TLT = np.sqrt(makeList("accp_edtm")/yield_dict["sent_edtm_PS"]**2+makeList("accp_edtm")**2/yield_dict["sent_edtm_PS"]**4)
        #uncern_TLT = np.sqrt(yield_dict["sent_edtm_PS"]*.95*.05)
        yield_dict.update({"uncern_TLT" : uncern_TLT})
        
    
    if SHMS_PS != None:
        yield_dict.update({"rate_SHMS" : makeList("SHMSTRIG_scaler")/makeList("time")})
        yield_dict.update({"sent_edtm_PS" : makeList("sent_edtm")/SHMS_PS})
        yield_dict.update({"sent_edtm_SHMS" : makeList("sent_edtm")/SHMS_PS})
         
        yield_dict.update({"uncern_SHMS_evts_scaler" : np.sqrt(makeList("SHMSTRIG_scaler"))/makeList("SHMSTRIG_scaler")})
        yield_dict.update({"uncern_SHMS_evts_notrack" : np.sqrt(makeList("p_int_etotnorm_evts"))/makeList("p_int_etotnorm_evts")})
        yield_dict.update({"uncern_SHMS_evts_track" : np.sqrt(makeList("p_int_etottracknorm_evts"))/makeList("p_int_etottracknorm_evts")})

        pTLT = makeList("paccp_edtm")/yield_dict["sent_edtm_SHMS"]
        yield_dict.update({"pTLT" : pTLT})        

        # Accepted scalers; removed EDTM subtraction. There are EDTM in here but it won't be this value.
        #SHMS_scaler_accp = makeList("SHMSTRIG_scaler") #-yield_dict["sent_edtm_PS"]
        #SHMS_scaler_accp = makeList("SHMSTRIG_scaler")-yield_dict["sent_edtm_SHMS"]
        SHMS_scaler_accp = makeList("SHMSTRIG_scaler")-makeList("sent_edtm") # Returns reasonable yields
        yield_dict.update({"SHMS_scaler_accp" : SHMS_scaler_accp})
        
        yield_SHMS_scaler = (yield_dict["SHMS_scaler_accp"])/(makeList("charge"))
        yield_SHMS_notrack = (makeList("p_int_etotnorm_evts")*SHMS_PS)/(makeList("charge")*yield_dict["TLT"])
        yield_SHMS_track = (makeList("p_int_etottracknorm_evts")*SHMS_PS)/(makeList("charge")*yield_dict["TLT"]*makeList("SHMS_track"))
        yield_SHMS_CPULT_notrack = (makeList("p_int_etotnorm_evts")*SHMS_PS)/(makeList("charge")*yield_dict["CPULT_phys"])
        yield_SHMS_CPULT_track = (makeList("p_int_etottracknorm_evts")*SHMS_PS)/(makeList("charge")*yield_dict["CPULT_phys"]*makeList("SHMS_track"))
        yield_dict.update({"yield_SHMS_scaler" : yield_SHMS_scaler})
        yield_dict.update({"yield_SHMS_notrack" : yield_SHMS_notrack})
        yield_dict.update({"yield_SHMS_track" : yield_SHMS_track})
        yield_dict.update({"yield_SHMS_CPULT_notrack" : yield_SHMS_CPULT_notrack})
        yield_dict.update({"yield_SHMS_CPULT_track" : yield_SHMS_CPULT_track})

        # Define relative yield relative to minimum current
        for i,curr in enumerate(yield_dict["current"]):
            if curr == min(yield_dict["current"]):
                min_yield_SHMS_scaler = yield_dict["yield_SHMS_scaler"][i]
                min_yield_SHMS_notrack = yield_dict["yield_SHMS_notrack"][i]
                min_yield_SHMS_track = yield_dict["yield_SHMS_track"][i]
        yield_dict.update({"min_yield_SHMS_scaler" : min_yield_SHMS_scaler})                
        yield_dict.update({"min_yield_SHMS_notrack" : min_yield_SHMS_notrack})
        yield_dict.update({"min_yield_SHMS_track" : min_yield_SHMS_track})

        # Define relative yield relative to minimum current
        for i,curr in enumerate(yield_dict["current"]):
            if curr == min(yield_dict["current"]):
                min_yield_SHMS_CPULT_notrack = yield_dict["yield_SHMS_CPULT_notrack"][i]
                min_yield_SHMS_CPULT_track = yield_dict["yield_SHMS_CPULT_track"][i]             
        yield_dict.update({"min_yield_SHMS_CPULT_notrack" : min_yield_SHMS_CPULT_notrack})
        yield_dict.update({"min_yield_SHMS_CPULT_track" : min_yield_SHMS_CPULT_track})

        yieldRel_SHMS_scaler = yield_dict["yield_SHMS_scaler"]/yield_dict["min_yield_SHMS_scaler"]
        yieldRel_SHMS_notrack = yield_dict["yield_SHMS_notrack"]/yield_dict["min_yield_SHMS_notrack"]
        yieldRel_SHMS_track = yield_dict["yield_SHMS_track"]/yield_dict["min_yield_SHMS_track"]
        yield_dict.update({"yieldRel_SHMS_scaler" : yieldRel_SHMS_scaler})
        yield_dict.update({"yieldRel_SHMS_notrack" : yieldRel_SHMS_notrack})
        yield_dict.update({"yieldRel_SHMS_track" : yieldRel_SHMS_track})
        
        yieldRel_SHMS_CPULT_notrack = yield_dict["yield_SHMS_CPULT_notrack"]/yield_dict["min_yield_SHMS_CPULT_notrack"]
        yieldRel_SHMS_CPULT_track = yield_dict["yield_SHMS_CPULT_track"]/yield_dict["min_yield_SHMS_CPULT_track"]
        yield_dict.update({"yieldRel_SHMS_CPULT_notrack" : yieldRel_SHMS_CPULT_notrack})
        yield_dict.update({"yieldRel_SHMS_CPULT_track" : yieldRel_SHMS_CPULT_track})

        uncern_yieldRel_SHMS_scaler = (yield_dict["uncern_SHMS_evts_scaler"]+yield_dict["uncern_CPULT_phys"])
        uncern_yieldRel_SHMS_notrack = (yield_dict["uncern_SHMS_evts_notrack"]+yield_dict["uncern_TLT"])
        uncern_yieldRel_SHMS_track =  (yield_dict["uncern_SHMS_evts_notrack"]+yield_dict["uncern_TLT"]+makeList("SHMS_track_uncern"))
        yield_dict.update({"uncern_yieldRel_SHMS_scaler" : uncern_yieldRel_SHMS_scaler})
        yield_dict.update({"uncern_yieldRel_SHMS_notrack" : uncern_yieldRel_SHMS_notrack})
        yield_dict.update({"uncern_yieldRel_SHMS_track" : uncern_yieldRel_SHMS_track})

        uncern_yieldRel_SHMS_CPULT_notrack = (yield_dict["uncern_SHMS_evts_notrack"]+yield_dict["uncern_CPULT_phys"])
        uncern_yieldRel_SHMS_CPULT_track =  (yield_dict["uncern_SHMS_evts_notrack"]+yield_dict["uncern_CPULT_phys"]+makeList("SHMS_track_uncern"))
        yield_dict.update({"uncern_yieldRel_SHMS_CPULT_notrack" : uncern_yieldRel_SHMS_CPULT_notrack})
        yield_dict.update({"uncern_yieldRel_SHMS_CPULT_track" : uncern_yieldRel_SHMS_CPULT_track})
        
        
    if HMS_PS != None:
        yield_dict.update({"rate_HMS" : makeList("HMSTRIG_scaler")/makeList("time")})
        yield_dict.update({"sent_edtm_PS" : makeList("sent_edtm")/HMS_PS})
        yield_dict.update({"sent_edtm_HMS" : makeList("sent_edtm")/HMS_PS})
         
        yield_dict.update({"uncern_HMS_evts_scaler" : np.sqrt(makeList("HMSTRIG_scaler"))/makeList("HMSTRIG_scaler")})
        yield_dict.update({"uncern_HMS_evts_notrack" : np.sqrt(makeList("p_int_etotnorm_evts"))/makeList("p_int_etotnorm_evts")})
        yield_dict.update({"uncern_HMS_evts_track" : np.sqrt(makeList("p_int_etottracknorm_evts"))/makeList("p_int_etottracknorm_evts")})

        hTLT = makeList("haccp_edtm")/yield_dict["sent_edtm_HMS"]
        yield_dict.update({"hTLT" : hTLT})

        # Accepted scalers; removed EDTM subtraction. There are EDTM in here but it won't be this value.
        #HMS_scaler_accp = makeList("HMSTRIG_scaler") #-yield_dict["sent_edtm_PS"]
        #HMS_scaler_accp = makeList("HMSTRIG_scaler")-yield_dict["sent_edtm_HMS"]
        HMS_scaler_accp = makeList("HMSTRIG_scaler")-makeList("sent_edtm") # Returns reasonable yields    
        yield_dict.update({"HMS_scaler_accp" : HMS_scaler_accp})

        # Calculate yield values
        yield_HMS_scaler = (yield_dict["HMS_scaler_accp"])/(makeList("charge"))
        yield_HMS_notrack = (makeList("h_int_etotnorm_evts")*HMS_PS)/(makeList("charge")*yield_dict["TLT"])
        yield_HMS_track = (makeList("h_int_etottracknorm_evts")*HMS_PS)/(makeList("charge")*yield_dict["TLT"]*makeList("HMS_track"))
        yield_HMS_CPULT_notrack = (makeList("h_int_etotnorm_evts")*HMS_PS)/(makeList("charge")*yield_dict["CPULT_phys"])
        yield_HMS_CPULT_track = (makeList("h_int_etottracknorm_evts")*HMS_PS)/(makeList("charge")*yield_dict["CPULT_phys"]*makeList("HMS_track"))
        yield_dict.update({"yield_HMS_scaler" : yield_HMS_scaler})
        yield_dict.update({"yield_HMS_notrack" : yield_HMS_notrack})
        yield_dict.update({"yield_HMS_track" : yield_HMS_track})
        yield_dict.update({"yield_HMS_CPULT_notrack" : yield_HMS_CPULT_notrack})
        yield_dict.update({"yield_HMS_CPULT_track" : yield_HMS_CPULT_track})

        # Define relative yield relative to minimum current
        for i,curr in enumerate(yield_dict["current"]):
            if curr == min(yield_dict["current"]):
                min_yield_HMS_scaler = yield_dict["yield_HMS_scaler"][i]
                min_yield_HMS_notrack = yield_dict["yield_HMS_notrack"][i]
                min_yield_HMS_track = yield_dict["yield_HMS_track"][i]
        yield_dict.update({"min_yield_HMS_scaler" : min_yield_HMS_scaler})                
        yield_dict.update({"min_yield_HMS_notrack" : min_yield_HMS_notrack})
        yield_dict.update({"min_yield_HMS_track" : min_yield_HMS_track})

        # Define relative yield relative to minimum current
        for i,curr in enumerate(yield_dict["current"]):
            if curr == min(yield_dict["current"]):
                min_yield_HMS_CPULT_notrack = yield_dict["yield_HMS_CPULT_notrack"][i]
                min_yield_HMS_CPULT_track = yield_dict["yield_HMS_CPULT_track"][i]             
        yield_dict.update({"min_yield_HMS_CPULT_notrack" : min_yield_HMS_CPULT_notrack})
        yield_dict.update({"min_yield_HMS_CPULT_track" : min_yield_HMS_CPULT_track})

        yieldRel_HMS_scaler = yield_dict["yield_HMS_scaler"]/yield_dict["min_yield_HMS_scaler"]
        yieldRel_HMS_notrack = yield_dict["yield_HMS_notrack"]/yield_dict["min_yield_HMS_notrack"]
        yieldRel_HMS_track = yield_dict["yield_HMS_track"]/yield_dict["min_yield_HMS_track"]
        yield_dict.update({"yieldRel_HMS_scaler" : yieldRel_HMS_scaler})
        yield_dict.update({"yieldRel_HMS_notrack" : yieldRel_HMS_notrack})
        yield_dict.update({"yieldRel_HMS_track" : yieldRel_HMS_track})

        yieldRel_HMS_CPULT_notrack = yield_dict["yield_HMS_CPULT_notrack"]/yield_dict["min_yield_HMS_CPULT_notrack"]
        yieldRel_HMS_CPULT_track = yield_dict["yield_HMS_CPULT_track"]/yield_dict["min_yield_HMS_CPULT_track"]
        yield_dict.update({"yieldRel_HMS_CPULT_notrack" : yieldRel_HMS_CPULT_notrack})
        yield_dict.update({"yieldRel_HMS_CPULT_track" : yieldRel_HMS_CPULT_track})

        uncern_yieldRel_HMS_scaler = (yield_dict["uncern_HMS_evts_scaler"]+yield_dict["uncern_CPULT_phys"])
        uncern_yieldRel_HMS_notrack = (yield_dict["uncern_HMS_evts_notrack"]+yield_dict["uncern_TLT"])
        uncern_yieldRel_HMS_track =  (yield_dict["uncern_HMS_evts_notrack"]+yield_dict["uncern_TLT"]+makeList("HMS_track_uncern"))
        yield_dict.update({"uncern_yieldRel_HMS_scaler" : uncern_yieldRel_HMS_scaler})
        yield_dict.update({"uncern_yieldRel_HMS_notrack" : uncern_yieldRel_HMS_notrack})
        yield_dict.update({"uncern_yieldRel_HMS_track" : uncern_yieldRel_HMS_track})

        uncern_yieldRel_HMS_CPULT_notrack = (yield_dict["uncern_HMS_evts_notrack"]+yield_dict["uncern_CPULT_phys"])
        uncern_yieldRel_HMS_CPULT_track =  (yield_dict["uncern_HMS_evts_notrack"]+yield_dict["uncern_CPULT_phys"]+makeList("HMS_track_uncern"))
        yield_dict.update({"uncern_yieldRel_HMS_CPULT_notrack" : uncern_yieldRel_HMS_CPULT_notrack})
        yield_dict.update({"uncern_yieldRel_HMS_CPULT_track" : uncern_yieldRel_HMS_CPULT_track})
        
    if COIN_PS != None:
        yield_dict.update({"rate_COIN" : makeList("COINTRIG_scaler")/makeList("time")})

        COIN_scaler_accp = makeList("COINTRIG_scaler") -yield_dict["sent_edtm_PS"] # This EDTM subtraction is fine because COIN are not PS and get EDTM first
        yield_dict.update({"COIN_scaler_accp" : COIN_scaler_accp})        
        
    #for i,psmod in enumerate(yield_dict["PS_mod"]):
    #    if psmod > 0:
    #        yield_dict["sent_edtm_PS"][i] = yield_dict["sent_edtm_PS_corr"][i]
        #else:
         #   sent_edtm_PS_final[i] = yield_dict["sent_edtm_PS"][i]            
    #yield_dict.update({"sent_edtm_PS_final" : sent_edtm_PS_final})

    # Restructure dictionary to dataframe format so it matches lumi_data
    yield_table = pd.DataFrame(yield_dict, columns=yield_dict.keys())
    yield_table = yield_table.reindex(sorted(yield_table.columns), axis=1)

    return yield_table

def mergeDicts():
    '''
    Merge dictionaries/dataframes, convert to dataframe and sort
    '''
    yield_data = calc_yield()
    # data = {**lumi_data, **yield_data} # only python 3.5+
    
    for key, val in lumi_data.items():
        lumi_data[key] = val

    datadict = {}
    for d in (lumi_data, yield_data): 
        datadict.update(d)
    data = {i : datadict[i] for i in sorted(datadict.keys())}

    table  = pd.DataFrame(data, columns=data.keys())
    table = table.reindex(sorted(table.columns), axis=1)

    return table

################################################################################################################################################

def plot_yield():
    '''
    Plot yields and various other analysis plots
    '''
    yield_data = mergeDicts()

    # Remove runs with bad TLT, print statement only
    for i,row in yield_data.iterrows():
        if row['TLT'] <= 0.75 or row['TLT'] > 1.02:
            print('''
            Removing {0:.0f} because TLT is low...
            TLT={1:0.2f} %
            CPULT={2:0.2f} %
            '''.format(row["run number"],row["TLT"]*100,row["CPULT_phys"]*100))
        if row['time'] < 60.0:
            print('''
            Removing {0:.0f} because beam on time is short...
            time={1:0.1f} s
            '''.format(row["run number"],row["time"]))

    # Remove runs with bad TLT or short on beam time
    #yield_data = yield_data[ (yield_data['TLT'] >= 0.75) & (yield_data['CPULT_phys'] >= 0.75) ].reset_index(drop=True)
    #yield_data = yield_data[ (yield_data['TLT'] < 1.02) & (yield_data['CPULT_phys'] < 1.02)].reset_index(drop=True)
    yield_data = yield_data[ (yield_data['time'] >= 60.0) ].reset_index(drop=True)

    for i, val in enumerate(yield_data["run number"]):
        print("Run numbers:",yield_data["run number"][i],"Current Values:",yield_data["current"][i])
    
    relYieldPlot = plt.figure(figsize=(12,8))

    #HMS plot scaler
    plt.subplot(2,3,1)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_scaler"],yerr=yield_data["yieldRel_HMS_scaler"]*yield_data["uncern_yieldRel_HMS_scaler"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_scaler"],color='blue',zorder=4)
    plt.ylabel('Rel. Yield Scaler', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #HMS plot no track
    plt.subplot(2,3,2)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_notrack"],yerr=yield_data["yieldRel_HMS_notrack"]*yield_data["uncern_yieldRel_HMS_notrack"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_notrack"],color='blue',zorder=4)
    #plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_CPULT_notrack"],yerr=yield_data["yieldRel_HMS_CPULT_notrack"]*yield_data["uncern_yieldRel_HMS_CPULT_notrack"],color='black',linestyle='None',zorder=5)
    #plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_CPULT_notrack"],color='red',zorder=6)
    plt.ylabel('Rel. Yield no track', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #HMS plot track
    plt.subplot(2,3,3)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_track"],yerr=yield_data["yieldRel_HMS_track"]*yield_data["uncern_yieldRel_HMS_track"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_track"],color='blue',zorder=4)
    #plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_CPULT_track"],yerr=yield_data["yieldRel_HMS_CPULT_track"]*yield_data["uncern_yieldRel_HMS_CPULT_track"],color='black',linestyle='None',zorder=5)
    #plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_CPULT_track"],color='red',zorder=6)
    plt.ylabel('Rel. Yield track', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

        
    #SHMS plot scaler
    plt.subplot(2,3,4)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_scaler"],yerr=yield_data["yieldRel_SHMS_scaler"]*yield_data["uncern_yieldRel_SHMS_scaler"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_scaler"],color='blue',zorder=4)
    plt.ylabel('Rel. Yield Scaler', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #SHMS plot no track
    plt.subplot(2,3,5)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_notrack"],yerr=yield_data["yieldRel_SHMS_notrack"]*yield_data["uncern_yieldRel_SHMS_notrack"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_notrack"],color='blue',zorder=4)
    #plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_CPULT_notrack"],yerr=yield_data["yieldRel_SHMS_CPULT_notrack"]*yield_data["uncern_yieldRel_SHMS_CPULT_notrack"],color='black',linestyle='None',zorder=5)
    #plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_CPULT_notrack"],color='red',zorder=6)
    plt.ylabel('Rel. Yield no track', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #SHMS plot track
    plt.subplot(2,3,6)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_track"],yerr=yield_data["yieldRel_SHMS_track"]*yield_data["uncern_yieldRel_SHMS_track"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_track"],color='blue',zorder=4)
    #plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_CPULT_track"],yerr=yield_data["yieldRel_SHMS_CPULT_track"]*yield_data["uncern_yieldRel_SHMS_CPULT_track"],color='black',linestyle='None',zorder=5)
    #plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_CPULT_track"],color='red',zorder=6)
    plt.ylabel('Rel. Yield track', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    plt.tight_layout()
    plt.savefig(SCRIPTPATH+'/luminosity/OUTPUTS/plots/Yield_%s_%s.png' % (out_f.split("yield_data_")[1].replace(".csv",""),"relYieldPlot"))
            

    #########################################################################################################################################################

    edtmPlot = plt.figure(figsize=(12,8))

    #Ratio accp/total scaler vs current
    plt.subplot(2,3,1)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.scatter(yield_data["current"],(yield_data["HMS_scaler_accp"]+yield_data["SHMS_scaler_accp"])/(yield_data["HMSTRIG_scaler"]+yield_data["SHMSTRIG_scaler"]),color='blue',zorder=4)
    plt.ylabel('Accp/Total scaler count', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #Scaler EDTM rate vs current
    plt.subplot(2,3,2)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.scatter(yield_data["current"],yield_data["sent_edtm"]/yield_data["time"],color='blue',zorder=4)
    plt.scatter(yield_data["current"],yield_data["sent_edtm_PS"]/yield_data["time"],color='red',zorder=4)
    plt.ylabel('Scaler EDTM rate [Hz]', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #EDTM vs HMS Rate
    plt.subplot(2,3,3)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.scatter(yield_data["rate_HMS"]/1000,yield_data["accp_edtm"]/(yield_data["time"]*1000),color='blue',zorder=4)
    plt.ylabel('EDTM Rate [kHz]', fontsize=16)
    plt.xlabel('HMS Rate [kHz]', fontsize =16)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #TLT vs Current
    plt.subplot(2,3,4)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.errorbar(yield_data["current"],yield_data["TLT"],yerr=yield_data["TLT"]*yield_data["uncern_TLT"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["TLT"],color='blue',zorder=4)
    plt.ylabel('TLT', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    #Time vs current
    plt.subplot(2,3,5)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.scatter(yield_data["current"],yield_data["time"]/60,color='blue',zorder=4)
    plt.ylabel('Time [min]', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =16)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)


    #EDTM vs SHMS Rate
    plt.subplot(2,3,6)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.scatter(yield_data["rate_SHMS"]/1000,yield_data["accp_edtm"]/(yield_data["time"]*1000),color='blue',zorder=4)
    plt.ylabel('EDTM Rate [kHz]', fontsize=16)
    plt.xlabel('SHMS Rate [kHz]', fontsize =16)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =16)

    plt.tight_layout()             
    plt.savefig(SCRIPTPATH+'/luminosity/OUTPUTS/plots/Yield_%s_%s.png' % (out_f.split("yield_data_")[1].replace(".csv",""),"edtmPlot"))
            
    #########################################################################################################################################################

    logPlot = plt.figure(figsize=(12,8))

    #HMS plot scaler
    plt.subplot(2,4,1)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_scaler"],yerr=yield_data["yieldRel_HMS_scaler"]*yield_data["uncern_yieldRel_HMS_scaler"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_scaler"],color='blue',zorder=4)
    plt.ylabel('Rel. Yield Scaler', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =12)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #HMS plot track
    plt.subplot(2,4,2)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_HMS_track"],yerr=yield_data["yieldRel_HMS_track"]*yield_data["uncern_yieldRel_HMS_track"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_HMS_track"],color='blue',zorder=4)
    plt.ylabel('Rel. Yield track', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =12)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #HMS track eff vs HMS Rate
    plt.subplot(2,4,3)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.errorbar(yield_data["rate_HMS"]/1000,yield_data["HMS_track"],yerr=yield_data["HMS_track"]*yield_data["HMS_track_uncern"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["rate_HMS"]/1000,yield_data["HMS_track"],color='blue',zorder=4)
    plt.ylabel('HMS track eff', fontsize=16)
    plt.xlabel('HMS Rate [kHz]', fontsize =12)
    if target == 'LD2' :
        plt.title('HMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('HMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('HMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #TLT vs Current
    plt.subplot(2,4,4)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.errorbar(yield_data["current"],yield_data["TLT"],yerr=yield_data["TLT"]*yield_data["uncern_TLT"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["TLT"],color='blue',zorder=4)
    plt.ylabel('TLT', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =12)
    if target == 'LD2' :
        plt.title('LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #CPULT vs Current
    plt.subplot(2,4,8)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.errorbar(yield_data["current"],yield_data["CPULT_phys"],yerr=yield_data["CPULT_phys"]*yield_data["uncern_CPULT_phys"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["CPULT_phys"],color='blue',zorder=4)
    plt.ylabel('CPULT', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =12)
    if target == 'LD2' :
        plt.title('LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #SHMS plot scaler
    plt.subplot(2,4,5)    
    plt.grid(zorder=1)
    plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_scaler"],yerr=yield_data["yieldRel_SHMS_scaler"]*yield_data["uncern_yieldRel_SHMS_scaler"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_scaler"],color='blue',zorder=4)
    plt.ylabel('Rel. Yield Scaler', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =12)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #SHMS plot track
    plt.subplot(2,4,6)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    #plt.ylim(0.9,1.1)
    plt.plot([0,100], [1,1], 'r-',zorder=2)
    plt.errorbar(yield_data["current"],yield_data["yieldRel_SHMS_track"],yerr=yield_data["yieldRel_SHMS_track"]*yield_data["uncern_yieldRel_SHMS_track"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["current"],yield_data["yieldRel_SHMS_track"],color='blue',zorder=4)
    plt.ylabel('Rel. Yield track', fontsize=16)
    plt.xlabel('Current [uA]', fontsize =12)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    #SHMS track vs SHMS Rate
    plt.subplot(2,4,7)    
    plt.grid(zorder=1)
    #plt.xlim(0,100)
    plt.errorbar(yield_data["rate_SHMS"]/1000,yield_data["SHMS_track"],yerr=yield_data["SHMS_track"]*yield_data["SHMS_track_uncern"],color='black',linestyle='None',zorder=3)
    plt.scatter(yield_data["rate_SHMS"]/1000,yield_data["SHMS_track"],color='blue',zorder=4)
    plt.ylabel('SHMS track eff', fontsize=16)
    plt.xlabel('SHMS Rate [kHz]', fontsize =12)
    if target == 'LD2' :
        plt.title('SHMS LD2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    elif target == 'LH2' :
        plt.title('SHMS LH2 %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)
    else :
        plt.title('SHMS Carbon %s-%s' % (int(min(yield_data["run number"])),int(max(yield_data["run number"]))), fontsize =12)

    plt.tight_layout()
    plt.savefig(SCRIPTPATH+'/luminosity/OUTPUTS/plots/Yield_%s_%s.png' % (out_f.split("yield_data_")[1].replace(".csv",""),"logPlot"))
            
    #plt.show()

    print("\nYield info...\n",yield_data[["run number","yieldRel_HMS_scaler","yieldRel_SHMS_scaler","yieldRel_HMS_notrack","yieldRel_SHMS_notrack","yieldRel_HMS_track","yieldRel_SHMS_track"]])

    return yield_data

################################################################################################################################################

def debug():
    '''
    Prints various values to debug, customize to your heart's content
    '''
    data = mergeDicts()
    print("\n\n=======================")
    print("DEBUG data")
    print("=======================")
    ### Debug prints
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(data[["run number","PS1","PS3","sent_edtm","sent_edtm_PS","sent_edtm_HMS","sent_edtm_SHMS","accp_edtm","TLT","CPULT_phys","current","time","HMS_track","SHMS_track"]])
   # print("EDTM scaler rate: ", data["sent_edtm"]/data["time"])
   # print("Accepted EDTM rate: ", data["accp_edtm"]/data["time"])
   # print("Run numbers: ", data["run number"].sort_values())
   # print("HMS scaler ratio",data["HMS_scaler_accp"]/data["HMSTRIG_scaler"])
   # print("SHMS scaler ratio",data["SHMS_scaler_accp"]/data["SHMSTRIG_scaler"])
    print("HMS Cal etotnorm\n",data[["h_int_etotnorm_evts","current"]])
    print("SHMS Cal etotnorm\n",data[["p_int_etotnorm_evts","current"]])
    print("HMS yield no track\n",data["yield_HMS_notrack"])
    print("SHMS yield no track\n",data["yield_SHMS_notrack"])
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print("\n\nHMS track uncertanties\n",data[["current","uncern_HMS_evts_notrack", "uncern_TLT", "uncern_CPULT_phys", "HMS_track_uncern"]])
        print("\n\nSHMS track uncertanties\n",data[["current","uncern_SHMS_evts_notrack", "uncern_TLT", "uncern_CPULT_phys", "SHMS_track_uncern"]])
    print("\n\nHMS yield track uncern\n",data["uncern_yieldRel_HMS_track"])
    print("SHMS yield track uncern\n",data["uncern_yieldRel_SHMS_track"])
    ###
    print("=======================\n\n")

################################################################################################################################################

def main():

    #debug()

    # Plot yields
    yield_data = plot_yield()

    table = mergeDicts()
    
    file_exists = os.path.isfile(out_f)

    table.to_csv(out_f, index=False, header=True, mode='w+',)

if __name__ == '__main__':
    main()
