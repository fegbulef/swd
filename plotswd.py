#!/usr/bin/python3

"""********************************************************************
Created by:   Fiona Egbulefu (Contractor)

Created date: 13 June 2019

Description:  Plot KPI charts
             
********************************************************************"""

import os
import sys
import time

import util  # user defined

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
swdlog = util.get_logger("swdlog")

barcolors = ['royalblue','darkorange','darkgray','gold','lightcoral','darkseagreen','navy','firebrick','mediumpurple']
stackcolors = ['royalblue','darkorange','darkgray','gold','cornflowerblue','darkseagreen','navy','firebrick','mediumpurple']
releasecolors = ['royalblue','darkorange','darkgray','gold','deepskyblue','darkseagreen','navy','firebrick','mediumpurple']
        

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
    
    filename = os.path.join(cwd, 'swdout', figname)

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
# Set range of custom colors
# ---------------------------------------------------------------
def get_custom_colormap(plot_type, index_range, by_release):

    if by_release:
        colormap = releasecolors[:index_range]
    else:
        if plot_type == 'bar':
            colormap = barcolors[:index_range]
        else:
            colormap = stackcolors[:index_range]
    
    return colormap


#----------------------------------------------------------------
# Plot bar chart for 6 months data
# - returns string (chart name)
#----------------------------------------------------------------
def plot_bar_chart(df, product, period):
    
    swdlog.info("Plotting bar chart {0} {1} .....".format(product, period))

    try:
        
        #****************#
        # plot downloads #
        #****************#

        width = 0.5
        figsize = (12,8)
        
        if period == '6M':
            figsize = (14,8)

        by_release = True if 'ReleaseNo' in df.columns.values.tolist() else False   
        colormap = get_custom_colormap('bar', len(df.columns), by_release)

        ax = df.plot(kind='bar', figsize=figsize, width=width, color=colormap, legend=False)

        fig = plt.gcf()
        plt.grid('on', linestyle='--', alpha=0.5)

        # get Cisco fonts
        fontproperties = get_Cisco_font()   
            
        # set xticklabels
        months = df.index.values.tolist()       # date labels    
        ax.set_xticklabels(months, rotation=360)
        set_ticklabels(ax.get_xticklabels())

        # set yticklabels
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))

        ybot, ytop = ax.get_ylim()
        if ytop <= 10:
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            for t in ax.yaxis.get_majorticklabels():
                if t == 0: t.set_visible(False)

        ax.set_ylim(bottom=0, top=ytop)

        set_ticklabels(ax.get_yticklabels())
            
        # annotate bars with bar value
        rects = ax.patches
        for rect in rects:
            ht = rect.get_height()
            label = "{:d}".format(int(ht))
            ax.text(rect.get_x()+rect.get_width()/2, ht, label, ha='center', va='bottom', fontweight='bold')
 
        plt.tight_layout()

        # save chart
        savefile = get_filename(product, period)
        fig.savefig(savefile)
        
        plt.close(fig)

        #plt.show()

    except Exception as e:
        
        swdlog.error("Could not create chart for {0} {1}: \n {2}".format(product, period, format(str(e))))
        return None

    return savefile


#----------------------------------------------------------------
# Plot stack chart for all data
# - returns string (chart name)
#----------------------------------------------------------------
def plot_stacked_chart(df, product, period):
    
    swdlog.info("Plotting stacked chart {0} {1} .....".format(product, period))

    try:
        
        #****************#
        # plot releases  #
        #****************#

        width = 0.5
        figsize = (12,8)

        # customize width and size of plot
        if period[-1] in ['D', 'W']:
            width = 0.75
            if 'all' in period:
                figsize = (18,9)
                
        by_release = True if 'ReleaseNo' in df.columns.values.tolist() else False    
        colormap = get_custom_colormap('stack', len(df.columns), by_release)
            
        ax = df.plot(kind='bar', stacked=True, figsize=figsize, width=width, color=colormap, legend=False)
        
        fig = plt.gcf()
        plt.grid('on', linestyle='--', alpha=0.5)

        fontproperties = get_Cisco_font()   

        months = df.index.values.tolist()   # date labels 
            
        # set xticklabels
        if period == "6M":            
            ax.set_xticklabels(months, rotation=360)
            set_ticklabels(ax.get_xticklabels())
            
        elif period in ["12M", "18M", "6W"]:
            set_ticklabels(ax.get_xticklabels())
            
        else:
            interval = 7        # show labels at 7 days/weeks 
            ax.set_xticks(ax.get_xticks()[::interval])
            xlabels = [m for i, m in enumerate(months) if i%interval ==0]
            ax.set_xticklabels(xlabels)
            set_ticklabels(ax.get_xticklabels())
         
        # set yticklabels
        yticks = ax.get_yticks().tolist()
        ax.set_ylim(bottom=0, top=max(yticks))
        set_ticklabels(ax.get_yticklabels())

        plt.tight_layout()

        # save chart
        savefile = get_filename(product, period)
        fig.savefig(savefile)
        
        plt.close(fig)


    except Exception as e:
        
        swdlog.error("Could not create chart for {0} {1}: \n {2}".format(product, period, format(str(e))))
        return None

    return savefile

