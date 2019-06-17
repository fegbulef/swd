#!/usr/bin/python3

"""********************************************************************
Created by:   Fiona Egbulefu (Contractor)

Created date: 13 June 2019

Description:  Plot KPI charts
             
********************************************************************"""

import os
import sys
import time

import logger  # user defined

try:
    import xlrd
    import numpy as np
    import pandas as pd

    import matplotlib 
    matplotlib.use('Agg')
    
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    
except ImportError:
    print("Please make sure the following modules are installed: 'pandas'; 'matplotlib'")
    sys.exit(-1)


# constants
dlog = logger.get_logger("downloads")
colors = ['royalblue','darkorange','grey','gold','lightcoral','yellowgreen','mediumpurple','blue','navy','firebrick']
        

#----------------------------------------------------------------
# Setup Cisco fonts
# - returns fontproperties object
#----------------------------------------------------------------
def get_Cisco_font():

    cwd = os.getcwd()
    
    fontpath = os.path.join(cwd, "CiscoFonts", "CiscoSansTTRegular.ttf")
    fontproperties = matplotlib.font_manager.FontProperties(fname=fontpath)
    
    return fontproperties

   
#----------------------------------------------------------------
# Derive chart name
# - returns string (filename)
#----------------------------------------------------------------
def get_filename(product, chartname):

    cwd = os.getcwd()
    figname = ''.join(['SWDL_', product, '_', chartname, '.png'])
    
    filename = os.path.join(cwd, 'downloads_out', figname)

    if os.path.exists(filename):
        os.remove(filename)
        time.sleep(2)   # make sure file is deleted 

    return filename


#----------------------------------------------------------------
# Set ticklabel fonts
# - returns None
#----------------------------------------------------------------
def set_ticklabels(ticklabels):

    for ticklabel in ticklabels:
        ticklabel.set_fontproperties(get_Cisco_font())
        ticklabel.set_fontsize(12)

    return


#----------------------------------------------------------------
# Plot bar chart for 6 months data
# - returns string (chart name)
#----------------------------------------------------------------
def plot_bars_by_month(df, product):
    
    dlog.info("Plotting monthly chart for {0} ......".format(product))

    try:
        
        #****************#
        # plot releases  #
        #****************#
        
        ax = df.plot(kind='bar', figsize=(14,8), width=0.55)    # plot 6 months of data

        fig = plt.gcf()
        plt.grid('on', linestyle='--', alpha=0.5)

        months = df.index.values.tolist()           # xticks labels    

        # set title font and sizes
        fontproperties = get_Cisco_font()   
        chart_title = "All XXX Releases for last 6 Months".replace('XXX', product)
        plt.title(chart_title, color='black', fontproperties=fontproperties, size=18, pad=-0.5)
            
        # set ticklabels font properties
        ax.set_xticklabels(months, rotation=360)
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))
    
        set_ticklabels(ax.get_xticklabels())
        set_ticklabels(ax.get_yticklabels())

        ybot, ytop = ax.get_ylim()
        if ytop <= 10:
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            for t in ax.yaxis.get_majorticklabels():
                if t == 0: t.set_visible(False)
            
        # annotate bars with bar value
        rects = ax.patches
        for rect in rects:
            ht = rect.get_height()
            label = "{:d}".format(int(ht))
            ax.text(rect.get_x()+rect.get_width()/2, ht, label, ha='center', va='bottom', fontweight='bold')
            
        # sort legend labels
        h1, l1 = ax.get_legend_handles_labels()
        ax.legend([h1[i] for i in range(len(h1))], [' '.join([product, l1[i]]) for i in range(len(h1))], loc='upper right', prop=fontproperties, fontsize=14)
      
        plt.tight_layout()

        # save chart
        savefile = get_filename(product, '6M')
        fig.savefig(savefile)
        
        plt.close(fig)

        #plt.show()

    except Exception as e:
        
        dlog.error("Could not create chart for {0}: \n {1}".format(product, format(str(e))))
        return None

    return savefile


#----------------------------------------------------------------
# Plot stack chart for all data
# - returns string (chart name)
#----------------------------------------------------------------
def plot_stacks_by_month(df, product):
    
    dlog.info("Plotting monthly chart for {0} ......".format(product))

    try:
        
        #****************#
        # plot releases  #
        #****************#

        ax = df.plot(kind='bar', stacked=True, figsize=(10,8), width=0.4)

        fig = plt.gcf()
        plt.grid('on', linestyle='--', alpha=0.5)

        months = df.index.values.tolist()           # xticks labels    

        # set title font and sizes
        fontproperties = get_Cisco_font()   
        chart_title = "All XXX Releases - Last 12 Months".replace('XXX', product)
        plt.title(chart_title, color='black', fontproperties=fontproperties, size=18, pad=-0.5)
            
        # set ticklabels font properties
        ax.set_xticklabels(months, rotation=360)
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))
    
        set_ticklabels(ax.get_xticklabels())
        set_ticklabels(ax.get_yticklabels())

        ybot, ytop = ax.get_ylim()
        if ytop <= 10:
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            for t in ax.yaxis.get_majorticklabels():
                if t == 0: t.set_visible(False)
      
        # sort legend labels
        h1, l1 = ax.get_legend_handles_labels()
        ax.legend([h1[i] for i in range(len(h1))], [' '.join([product, l1[i]]) for i in range(len(h1))], loc='upper right', prop=fontproperties, fontsize=14)
      
        plt.tight_layout()

        # save chart
        savefile = get_filename(product, '12M')
        fig.savefig(savefile)
        
        plt.close(fig)

        #plt.show()

    except Exception as e:
        
        dlog.error("Could not create chart for {0}: \n {1}".format(product, format(str(e))))
        return None

    return savefile

