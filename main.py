#!/usr/bin/python3

"""********************************************************************
Created by:   Fiona Egbulefu (Contractor)

Created date: 10 June 2019

Description:  Main script to automate KPI charts for 'Downloads'
              - Calls module to import raw data
              - Calls module to build charts

********************************************************************"""

import os
import sys
import json

import requests
import warnings

from datetime import datetime

try:
    import pandas as pd
    
except ImportError:
    print("Please install the python 'pandas' and 'xlrd' modules")
    sys.exit(-1)

# user defined modules
import logger
import plotdownloads
import importdownloads



#****************************
# Downloads constants
#****************************

downloads_file = r'data\SWDL_Sample.xlsx'
downloads_sheet = r'SWDownloads-123'        #'SW_Downloads_by_Filename-8'

products = {'CMS': 'Server', 'CMM': 'Management', 'CMA': 'Client'}


#-------------------------------------------------------------
# Find release/version number within filename
# - returns string (release/version)
#-------------------------------------------------------------
def get_release_number(file):

    num = ''
    release = ''
    
    for i, c in enumerate(file):

        # build version number
        if c.isdigit():
            num = ''.join([num, c])
            continue

        # build release number
        if num:
            release = num if release == '' else ''.join([release, '.', num])

            if len(release.split('.')) == 2:   # release/version complete e.g. 2.0
                break

            num = ''    # reset num

    return release


#-------------------------------------------------------------
# Get data for downloads
# - returns Dataframe structure
#-------------------------------------------------------------
def group_data_by_month_and_release(df_product):

    productgrp = {}

    # build dict by date
    for i in df_product.index:
        month = df_product.DownloadMonth[i]
        file = df_product.DownloadFile[i]

        if not month in productgrp:
            productgrp[month] = {}

        # get release/version count
        release = get_release_number(file)
        if not release in productgrp[month]:
            productgrp[month][release] = 1
        else:
            productgrp[month][release] += 1 
    
    # convert to dataframe
    df = pd.DataFrame(productgrp)
    df = df.transpose()    # place dates as row headers

    # sort columns by release
    cols = df.columns.values.tolist()
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            if int(cols[i].replace('.','')) > int(cols[j].replace('.','')):
                temp = cols[i]
                cols[i], cols[j] = cols[j], temp


    df_download = df[cols]
    df_download.fillna(0, inplace=True) 
    
    dlog.debug("download group: {}".format(len(df_download)))
               
    return df_download

    
#-------------------------------------------------------------
# Get data for downloads
# - returns Dataframe structure
#-------------------------------------------------------------
def process_downloads(fromexcel=True):

    xlfile = os.path.join(os.getcwd(), downloads_file)

    # import data
    if fromexcel:
        import_df = importdownloads.import_from_excel(xlfile, downloads_sheet)
    else:
        import_df = importdownloads.import_from_api()


    if not import_df is None:

        downloads_df = importdownloads.filter_downloads(import_df)

        # get counts by product/ date(MMM-YYYY)/ version
        for pcode, pname in products.items():
            dlog.info("Processing {}:....".format(pcode))

            product_filter = downloads_df.apply(lambda x: x.Product == pcode, axis=1)
            df_product = downloads_df[product_filter]

            if len(df_product) == 0:
                dlog.warning("No data found for {}".format(pcode))
                
            else:
                df_plot = group_data_by_month_and_release(df_product)
                #print("\n\n{0} Download:\n {1}".format(pcode, df_plot))

                # plot last six months as bar chart
                plot_start = len(df_plot)-6
                kpi_chart = plotdownloads.plot_bars_by_month(df_plot[plot_start:], pcode)
                if kpi_chart:
                    dlog.info("Monthly chart created for {0}: {1}".format(pcode, kpi_chart))

                kpi_chart = plotdownloads.plot_stacks_by_month(df_plot, pcode)
                if kpi_chart:
                    dlog.info("yearly chart created for {0}: {1}".format(pcode, kpi_chart))
                    
    else:

        dlog.warning("No download data available!")


    return



#***********#
# M A I N   #
#***********#

dlog = logger.setup_logger("downloads", "swdlog.log")
dlog.info("Started.......")

process_downloads(fromexcel=True)

dlog.info("Finished!")
    
