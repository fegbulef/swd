#!/usr/bin/python3

"""********************************************************************
Created by:   Fiona Egbulefu (Contractor)

Created date: 10 June 2019

Description:  Import raw data for Downloads KPI automation
              - Imports from specified Excel sheets
              - Calls module to build charts

********************************************************************"""

import os
import sys
import json

import requests
import warnings

import logger   # user defined module

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

try:
    import numpy as np
    import pandas as pd
    
except ImportError:
    print("Please install the python 'pandas' and 'xlrd' modules")
    sys.exit(-1)


# Constants
#************
download_type = ['2 - Customer', '3 - Partner']

dlog = logger.get_logger("downloads")


#------------------------------------------------------------
# Get API status code description
# - returns string 
#------------------------------------------------------------
def api_status_code_desc(api):

    status_desc = ''

    if api.status_code == 200:
        status_desc = "OK"
    elif api.status_code == 204:
        status_desc = "No Content"
    elif api.status_code == 400:
        status_desc = "Bad Request"
    elif api.status_code == 401:
        status_desc = "Unauthorized User/Password"
    elif api.status_code == 403:
        status_desc = "No permission to make this request"
    elif api.status_code == 404:
        status_desc = "Source Not found"
    elif api.status_code == 405:
        status_desc = "Method Not Allowed"
    elif api.status_code == 429:
        status_desc = "Too Many Requests"
    elif api.status_code == 500:
        status_desc = "Internal Server Error"
    elif api.status_code == 503:
        status_desc = "Service Unavailable"
    else:
        status_desc = "Request Unsuccessfull"
            
    return status_desc


#-------------------------------------------------------------
# Import raw data using API for given tool 
# - returns DataFrame structure 
#-------------------------------------------------------------
def import_from_api():

    return None

#-------------------------------------------------------------
# Filter data by - 12 months of data and download type (above)
# - returns DataFrame structure 
#-------------------------------------------------------------
def apply_filters(df):

    # set start/end dates
    start_dt = date.today() - relativedelta(months=11)    # filter for 12 months of data incl
    dlog.debug("Start date: {0}".format(start_dt))

    # get last 12 months of data
    swdl_date = pd.to_datetime(df['Download Date and Time'], format="%d/%m/%Y %HH:%MM:%SS", errors='coerce')
    df = df.assign(DownloadDate=swdl_date)
    df_filtered = df[df.DownloadDate >= pd.Timestamp(start_dt)]

    # select only 'Customer' and 'Partner' records
    access_level = df_filtered.apply(lambda x: x['Access Level Name'] in download_type, axis=1)
    df_filtered = df_filtered[access_level]

    df_filtered.reset_index(inplace=True)
    
    return df_filtered


#-------------------------------------------------------------
# Filter, sort and group data by product - CMS / CMA / CMM 
# - returns DataFrame structure 
#-------------------------------------------------------------
def filter_downloads(import_df):

    # Filter data 
    df = apply_filters(import_df)

    # work out product type - CMS / CMA / CMM
    filename = df['Full File Name'].str.split('/').str[-1]
    filename = filename.str.replace('Cisco_Meeting_', '')

    product = [''] * len(filename)
    for i in filename.index:
        if 'Server' in filename[i]:
            product[i] = 'CMS'
        elif 'Management' in filename[i]:
            product[i] = 'CMM'
        else:
            product[i] = 'CMA'

    df = df.assign(DownloadFile=filename, Product=product)
    
    # set download date as 'month-year'
    download_datetime = pd.to_datetime(df['Download Date and Time'], format="%d/%m/%Y %HH:%MM:%SS", errors='coerce')
    download_month = download_datetime.dt.strftime("%b-%Y")

    df = df.assign(DownloadMonth=download_month)

    # sort data by Download Date by File
    df.sort_values(['DownloadDate','DownloadFile'], ascending=True, inplace=True)
    
    if 'index' in df.columns:      # drop index column created by assign
        df.drop('index', axis=1, inplace=True)   

    dlog.debug("Cleaned data: {}".format(len(df)))

    return df

    
#-------------------------------------------------------------
# Import data from a defined sheet in a given Excel workbook
# - returns DataFrame structure 
#-------------------------------------------------------------
def import_from_excel(xlfile, xlsheet):

    import_df = None

    if not xlfile or not xlsheet:
        dlog.error("Excel filename and sheetname required for import")
        return import_df
    
    try:
    
        # import Excel data from specific workbook and sheet; ignore xlrd warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            import_df = pd.read_excel(xlfile, xlsheet)
            
    except Exception as e:
        dlog.error("Exception: {}".format(str(e)))


    if not import_df is None:
        dlog.debug("Imported records: {}".format(len(import_df)))

    return import_df
