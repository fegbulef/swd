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


# ---------- #
# Constants  #
# ---------- #

PRODUCTS = {"CMS": "Cisco Meeting Server", "CMA": "Cisco Meeting App", "CMM": "Cisco Meeting Manager"}

PRODCOLORS = {"CMS":('cornflowerblue','blue'), "CMA":('darkorange','gold'), "CMM":('darkgray', 'black')}

BARCOLORS = ['royalblue','darkorange','darkgray','gold','lightcoral','darkseagreen','navy','firebrick','mediumpurple']
STACKCOLORS = ['royalblue','darkorange','darkgray','gold','cornflowerblue','darkseagreen','navy','firebrick','mediumpurple']

        
# setup log
swdllog = util.get_logger("swdllog")


#----------------------------------------------------------------
# Setup Cisco fonts
# - returns fontproperties object
#----------------------------------------------------------------
def get_custom_font():

    cwd = os.getcwd()
    
    fontpath = os.path.join(cwd, "CiscoFonts", "CiscoSansTTRegular.ttf")
    fontproperties = matplotlib.font_manager.FontProperties(fname=fontpath)
    
    return fontproperties

   
#----------------------------------------------------------------
# Setup plot: label fonts and fontsize
# return Plot Figure
#----------------------------------------------------------------
def setup_plot(product, period, xlim, plot_type):

    # set figsize
    if plot_type == 'bar':

        if product in PRODUCTS:
            figsize = (8,6)
        elif period == '6M':
            figsize = (14,8)
        else:
            figsize = (12,8)

    else:

        figsize = (12,8)
        if period[-1] in ['D', 'W']:
            if 'all' in period:
                figsize = (18,9)

    # create plot
    fig, ax = plt.subplots(figsize=figsize)

    custom_font = get_custom_font()     # use Cisco fonts

    if product in PRODUCTS:
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.grid(True, which='major', axis='y', linestyle='-', alpha=0.4)

        plt.title(PRODUCTS[product], color='darkgray', fontsize=16, fontproperties=custom_font)
        
    else:
        plt.grid('on', linestyle='--', alpha=0.5)
    
    ax.xaxis.get_label().set_fontproperties(custom_font)
    ax.yaxis.get_label().set_fontproperties(custom_font)

    for label in (ax.get_xticklabels() + ax .get_yticklabels()):
        label.set_fontproperties(custom_font)
        label.set_fontsize(10)
        
    return plt, fig, ax


#----------------------------------------------------------------
# Derive chart name
# - returns string (filename)
#----------------------------------------------------------------
def get_filename(product, chartname):

    cwd = os.getcwd()
    figname = ''.join(['SWDL_', product, '_', chartname, '.png'])
    
    filename = os.path.join(cwd, 'swdlout', figname)

    if os.path.exists(filename):
        os.remove(filename)
        time.sleep(2)   # make sure file is deleted 

    return filename


#----------------------------------------------------------------
# Set range of custom colors
# ---------------------------------------------------------------
def get_custom_colormap(plot_type, index_range, product):

##    if product in PRODUCTS:
##        if product == 'CMS':
##            index_range -= 3
##            colormap = [PRODCOLORS['CMS'][0]]*index_range + [PRODCOLORS['CMS'][1]]*3
##        else:
##            index_range -= 1
##            colormap = [PRODCOLORS[product][0]]*index_range + [PRODCOLORS[product][1]]
##
##    else:
    if plot_type == 'bar':
        colormap = BARCOLORS[:index_range]
    else:
        colormap = STACKCOLORS[:index_range]


    return colormap


#----------------------------------------------------------------
# Get totals for each release (across all months)
# ---------------------------------------------------------------
def get_release_totals(df):

    reltot = {}
    for r in df.columns.values.tolist():
        sum_r = int(df[r].sum())
        reltot[r] = str(sum_r)
   
    return reltot


#----------------------------------------------------------------
# Plot bar chart for 6 months data
# - returns string (chart name)
#----------------------------------------------------------------
def plot_bar_chart(df, product, period):
    
    swdllog.info("Plotting bar chart {0} {1} .....".format(product, period))

    try:
        
        #****************#
        # plot downloads #
        #****************#

        xlim = len(df)

        # determine if plot by product
        by_product = False
        if product in PRODUCTS:
            by_product = True
            
        if by_product:
            xlim = len(df.index.values.tolist())

        # setup plot    
        plt, fig, ax = setup_plot(product, period, xlim, 'bar')

        width = 0.5     # bar width
        colormap = get_custom_colormap('bar', xlim, product)
        
        ax = df.plot(ax=ax, kind='bar', width=width, color=colormap, legend=by_product)
             
        # set xlabels, xticklabels
        plt.xlabel(None)

        xaxis = df.index.values.tolist()       # date / releaseno    
        if not by_product:
            ax.set_xticklabels(xaxis, rotation=360)

        # set yticklabels
        ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%d"))

        ybot, ytop = ax.get_ylim()
        if ytop <= 10:
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
            for t in ax.yaxis.get_majorticklabels():
                if t == 0: t.set_visible(False)

        yticks = ax.get_yticks().tolist()
        ax.set_ylim(bottom=0, top=max(yticks))
            
        # annotate bars with bar value
        rects = ax.patches
        for i, rect in enumerate(rects):

            ht = rect.get_height()
            label = "{:d}".format(int(ht))
            fontweight = 'bold'

            # annotate current releases in bold
            if by_product:
                if product == 'CMS':
                    fontweight = 'bold' if i >= len(rects)-3 else 'normal'
                else:
                    fontweight = 'bold' if i == len(rects)-1 else 'normal'
            
            ax.text(rect.get_x()+rect.get_width()/2, ht, label, ha='center', va='bottom', fontweight=fontweight)
 
        plt.tight_layout()

        # save chart
        savefile = get_filename(product, period)
        fig.savefig(savefile)
        
        plt.close(fig)

    except Exception as e:
        
        swdllog.error("Could not create chart for {0} {1}: \n {2}".format(product, period, format(str(e))))
        return None

    return savefile


#----------------------------------------------------------------
# Plot stack chart for all data
# - returns string (chart name)
#----------------------------------------------------------------
def plot_stacked_chart(df, product, period):
    
    swdllog.info("Plotting stacked chart {0} {1} .....".format(product, period))

    try:
        
        #****************#
        # plot releases  #
        #****************#

        xlim = len(df.columns)

        # determine if plot by product
        by_product = False
        if product in PRODUCTS:
            by_product = True

        # get column totals
        if by_product:
            release_totals = get_release_totals(df)
    
        # setup plot    
        plt, fig, ax =setup_plot(product, period, xlim, 'stacked')

        width = 0.4     # bar width
        if period[-1] in ['D','W']:
            width = 0.75
            
        colormap = get_custom_colormap('stack', xlim, product)
        
        ax = df.plot(ax=ax, kind='bar', stacked=True, width=width, color=colormap, legend=by_product)
       
        xaxis = df.index.values.tolist()   # date labels
 
        # set xticklabels
        if period == "6M":            
            ax.set_xticklabels(xaxis, rotation=360)     # horizontal labels

        elif period[-1] in ['D', 'W']:

            # set interval to display labels
            interval = 7
            if period[:-1].isdigit():
                if int(period[:-1]) < 18:
                    interval = 4
             
            ax.set_xticks(ax.get_xticks()[::interval])
            xlabels = [m for i, m in enumerate(xaxis) if i%interval ==0]
            ax.set_xticklabels(xlabels)
         
        # set yticklabels
        yticks = ax.get_yticks().tolist()
        ax.set_ylim(bottom=0, top=max(yticks))          # for barh: remove

        # display totals against product release labels
        if by_product:
            legend = ax.legend()
            for text in legend.texts:
                rtext = str(text.get_text())
                if rtext in release_totals:
                    new_text = ''.join([rtext, ' (', release_totals[rtext], ')'])
                    text.set_text(new_text)

        plt.tight_layout()

        # save chart
        savefile = get_filename(product, period)
        fig.savefig(savefile)
        
        plt.close(fig)


    except Exception as e:
        
        swdllog.error("Could not create chart for {0} {1}: \n {2}".format(product, period, format(str(e))))
        return None

    return savefile

