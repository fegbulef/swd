#!/usr/bin/python3

"""********************************************************************
Created by:   Fiona Egbulefu (Contractor)

Created date: 10 June 2019

Description:  General routines to filter, format and prepare data for
              Software Downloads KPI automation

***********************************************************************"""

import os
import sys
import warnings

from datetime import timedelta, datetime, date

try:
    import numpy as np
    import pandas as pd
    
except ImportError:
    print("Please install the python 'pandas' and 'xlrd' modules")
    sys.exit(-1)


import util   # user defined module


# -------
# Setup
# -------

swdlog = util.get_logger("swdlog")

swd_type = ['1 - Registered Guest', '2 - Customer', '3 - Partner']


#-------------------------------------------------------------
# Return start/end dates for filtering 
#-------------------------------------------------------------
def get_start_end_dates(mths):

    end_dt = util.get_next_date(datetime(date.today().year, date.today().month, 1), 0, -1)
    start_dt = util.get_next_date(end_dt, mths, 0)
    start_dt = datetime(start_dt.year, start_dt.month, 1)   # get start of month
    
    return start_dt, end_dt


#-------------------------------------------------------------
# Return start/end weeks of DataFrame data 
#-------------------------------------------------------------
def get_start_end_weeks(df, datecol):

    # convert df dates to datetime
    dt = pd.to_datetime(str(min(list(df[datecol].values))))
    start_dt = datetime.strptime(dt.strftime("%d/%m/%Y"), "%d/%m/%Y")
    dt = pd.to_datetime(str(max(list(df[datecol].values))))
    end_dt = datetime.strptime(dt.strftime("%d/%m/%Y"), "%d/%m/%Y")

    swdlog.debug("Start week: {0} End week: {1}".format(start_dt, end_dt))
    
    return start_dt, end_dt


#----------------------------------------------------------------
# Return two lists with start/end of each week within givn dates  
#----------------------------------------------------------------
def get_period_weeks(start_dt, end_dt):

    # (Sun:6, Mon:0, Tue:1, Wed:2, Thu:3, Fri:4, Sat:5)
    if not start_dt.weekday() == 6:    
        days = 7 + (start_dt.weekday()-6)
        start_dt = util.get_next_date(start_dt, 0, -days)

    # get weekly dates between start/end : Sun to Sat
    wkstart = [start_dt + timedelta(days=d) for d in range(0, (end_dt-start_dt).days, 7)]
    wkend = [dt + timedelta(days=6) for dt in wkstart]

    return wkstart, wkend


#-------------------------------------------------------------
# Returned sorted dataframe by date column
#-------------------------------------------------------------
def sort_df_by_date(df, column, datefmt):

    dates = pd.to_datetime(df[column], format=datefmt, errors='coerce')
    df_sorted = df.assign(dates=dates)
    df_sorted.sort_values("dates", ascending=True, inplace=True)
    
    df_sorted.drop("dates", axis=1, inplace=True)

    return df_sorted


#-------------------------------------------------------------
# Grroup data by week
# - returns Dataframe structure
#-------------------------------------------------------------
def group_data_by_week(df, keydate, wkstart, wkend, keycol, keycnt):

    grp_data = {}
   
    for idx, wk in enumerate(wkstart):      # by week
        if not wk in grp_data:
            grp_data[wk] = {}

        for i in df.index:
            dt = df[keydate][i].date()
            key = df[keycol][i]

            if not key in grp_data[wk]:    # by Product / ReleaseNo
                grp_data[wk][key] = 0
        
            if (dt >= wk.date()) and (dt <= wkend[idx].date()):
                grp_data[wk][key] += df[keycnt][i]


    return grp_data


#-------------------------------------------------------------
# Group data by day/month
# - returns dict
#-------------------------------------------------------------
def group_data_by_day_month(df, keydate, keycol, keycnt):

    grp_data = {}

    for i in df.index:
        dt = df[keydate][i]
        key = df[keycol][i]

        # check for valid releaseno's
        if keycol == "ReleaseNo":
            if not key.replace('.','').isdigit():   # not a valid number
                continue

        if not dt in grp_data:          # by day/month
            grp_data[dt] = {}
        if not key in grp_data[dt]:     # by product / releaseno
            grp_data[dt][key] = 0
                
        grp_data[dt][key] += df[keycnt][i]

              
    return grp_data


#-------------------------------------------------------------
# Grroup products by day/week/month
# - returns Dataframe structure
#-------------------------------------------------------------
def group_data_by_date(df, period, grp_by_release=False):

    df_data = df

    # set start/end of period
    if period[-1] in ['D', 'M']:

        if not 'all' in period:
            mths = int(period[:-1])-1
            start_dt, end_dt = get_start_end_dates(-mths)
            df_data = df[(df.DownloadDate >= pd.to_datetime(start_dt)) & (df.DownloadDate <= pd.to_datetime(end_dt))]

    else:
        if 'all' in period:
            start_dt, end_dt = get_start_end_weeks(df_data, "DownloadDate")         
        else:
            mths = int(period[:-1])-1
            start_dt, end_dt = get_start_end_dates(-mths)

        swdlog.debug("By week period: {0} {1}".format(start_dt, end_dt))
        wkstart, wkend = get_period_weeks(start_dt, end_dt)

    # set key column for grouping data 
    keydate = "DownloadMonth"
    if period[-1] in ['D', 'W']:
        keydate = "DownloadDate"

    if grp_by_release:
        df_grp = df_data[[keydate, "ReleaseNo"]].groupby([keydate, "ReleaseNo"]).size().reset_index(name="ReleaseCnt")
    else:
        df_grp = df_data[[keydate, "Product"]].groupby([keydate, "Product"]).size().reset_index(name="ProductCnt")

    grp_data = {}

    # set key cols for regrouping
    if grp_by_release:
        keycol = "ReleaseNo"
        keycnt = "ReleaseCnt"
    else:
        keycol = "Product"
        keycnt = "ProductCnt"

    # reformat grouped data
    if period[-1] in ['D', 'M']:
        grp_data = group_data_by_day_month(df_grp, keydate, keycol, keycnt)
    else:
        grp_data = group_data_by_week(df_grp, keydate, wkstart, wkend, keycol, keycnt)

    df_grouped = pd.DataFrame(grp_data)
    df_grouped.fillna(0, inplace=True)
    #print("Grp:\n", df_grouped.head())

    # reformat dates colummns
    if period[-1] == 'D':

        datecols = list(df_grouped.columns.values)
        days = pd.DataFrame(datecols, columns=["Days"])
        days = days.Days.dt.strftime("%d-%b")       # dd-MMM
        df_grouped.columns = days.values.tolist()
                               
    elif period[-1] == 'M':

        dates = pd.DataFrame(df_grouped.columns.values.tolist(), columns=["Months"])
        df_sorted = sort_df_by_date(dates, "Months", "%b-%Y")
        df_grouped = df_grouped[df_sorted.Months.values.tolist()]

    else:       
        # set columns to: 'dd-MMM - dd-MMM'
        datecols = []
        for idx, wk in enumerate(wkstart):
            week = ''.join([wk.strftime("%d-%b"), ' - ', wkend[idx].strftime("%d-%b")])
            datecols.append(week)

        df_grouped.columns = datecols

    # place dates as row headers
    df_grouped = df_grouped.transpose()   
  
    # if grouping by release, sort release numbers and append product ('CMS') name
    if grp_by_release:
        rcols = pd.DataFrame(df_grouped.columns.values.tolist(), columns=["R"])
        rstr = 'CMS ' + rcols.R
        rcols = rcols.assign(R=rstr)
        df_grouped.columns = rcols.R.values.tolist()
    
    #print("\nGrouped data for", period, ":\n", df_grouped.head())
    return df_grouped
   

#-------------------------------------------------------------
# Filter data months and download type (as set above)
# - returns DataFrame structure 
#-------------------------------------------------------------
def apply_filters(df):

    # exclude pdf files
    pdf = df['Full File Name'].map(lambda x: x.endswith('.pdf'))
    df = df[~pdf]

    # exclude filenames with no version e.g. '../Cisco_Meeting.dmg'
    invalidfile = df['Full File Name'].map(lambda x: x.endswith('Cisco_Meeting.dmg'))
    df = df[~invalidfile]
    
    # set date filter: from 1-Aug-2016
    start_dt = datetime(2016, 8, 1)
    end_dt = util.get_next_date(datetime(date.today().year, date.today().month, 1), 0, -1)  # end of prev. month
    swdlog.debug("Filter dates: {0} - {1}".format(start_dt, end_dt))

    # get last 12 months of data
    swd_date = pd.to_datetime(df['Download Date and Time'], format="%d/%m/%Y %HH:%MM:%SS", errors='coerce')
    swd_date = swd_date.dt.normalize()  # display only date part
    df = df.assign(DownloadDate=swd_date)
    df_filtered = df[(df.DownloadDate >= pd.to_datetime(start_dt)) & (df.DownloadDate <= pd.to_datetime(end_dt))]

    # select only 'Customer' and 'Partner' records
    access_level = df_filtered.apply(lambda x: x['Access Level Name'] in swd_type, axis=1)
    df_filtered = df_filtered[access_level]

    df_filtered.reset_index(inplace=True)

    swdlog.debug("Filtered records: {0}".format(len(df_filtered)))
    
    return df_filtered


#-------------------------------------------------------------
# Split filename into parts that can be identified for  
#-------------------------------------------------------------
def decode_filename(df):

    df_dict = {}
    
    # initialise decode_df
    df_dict['Product'] = [None] * len(df)
    df_dict['PType'] = [None] * len(df)
    df_dict['R'] = [None] * len(df)
    df_dict['V'] = [None] * len(df)
    df_dict['M'] = [None] * len(df)
    df_dict['Ext'] = [None] * len(df)
    df_dict['Type'] = [None] * len(df)
    df_dict['MonthYear'] = [None] * len(df)
    
    # split filename into columns
    filesplit = pd.DataFrame(df.DownloadFile.str.split('_', 4, expand=True))
    filesplit.columns = ['Product', 'R', 'V', 'M', 'Ext']


    try:

        for i in filesplit.index:

            # assign ProductType and DownloadDate
            df_dict['PType'][i] = df.Product[i]
            df_dict['MonthYear'][i] = df.DownloadMonth[i]
 

            # decode Product and 'R'
            if filesplit.Product[i].isdigit(): 
                df_dict['Product'][i] = 'Client'
                df_dict['R'][i] = filesplit.Product[i]
                df_dict['V'][i] = filesplit.R[i]
                df_dict['M'][i] = filesplit.V[i]
                df_dict['Ext'][i] = filesplit.M[i]
            
            else:
                df_dict['Product'][i] = filesplit.Product[i]
                df_dict['R'][i] = filesplit.R[i]       # should always be valid - major version


            # decode 'V'
            if not filesplit.V[i] is None:

                if filesplit.V[i].isdigit():
                    df_dict['V'][i] = filesplit.V[i]

                else:
                    ver = filesplit.V[i].split('.')

                    if len(ver) > 1:
                        df_dict['V'][i] = ver[0]
                        df_dict['Type'][i] = ver[1]    
            else:
                df_dict['V'][i] = '0'


            # decode 'M'
            if not filesplit.M[i] is None:

                if filesplit.M[i].isdigit():

                    df_dict['M'][i] = filesplit.M[i]
                
                else:
                    ver = filesplit.M[i].split('.')

                    if ver[0].isdigit():
                        df_dict['M'][i] = ver[0]
                        df_dict['Type'][i] = ver[1]
                    else:
                        df_dict['M'][i] = '0'
                        df_dict['Ext'][i] = ver[0]
                        df_dict['Type'][i] = ver[1]
                    
            else:
                df_dict['M'][i] = '0'
        

            # decode 'Ext'
            if not filesplit.Ext[i] is None:
                ext = filesplit.Ext[i].split('.')
                df_dict['Ext'][i] = ext[0]
                df_dict['Type'][i] = ext[1]


    except Exception as e:
        swdlog.error("Unable to decode file - {}".format(str(e)))

    decode_df = pd.DataFrame(df_dict)
    decode_df.reset_index(inplace=True)
    
    swdlog.info("Downloadfile decoded records: {}".format(len(decode_df)))

    return decode_df


#-------------------------------------------------------------
# Decode and reformat downloadfile and export to CSV  
#-------------------------------------------------------------
def get_export_downloadfile(df):

    export_df = pd.DataFrame()
    decode_df = decode_filename(df)

    sep = "_"
    prodversion = [''] * len(decode_df)

    # join columns for Product/Version
    for i in decode_df.index:
    
        prodversion[i] = decode_df.Product[i] + sep + str(decode_df.R[i]) + sep + str(decode_df.V[i]) + sep + str(decode_df.M[i])

        if not decode_df.Ext[i] is None:
            prodversion[i] = prodversion[i] + sep + decode_df.Ext[i]


    export_df["ProductVersion"] = prodversion
    export_df["Product"] = decode_df.PType

    exts = list(set(decode_df.Ext.values.tolist()))     # get unique value of exts

    # place extension in different columns
    vsphere = [''] * len(decode_df)

    for ext in exts:
        if not ext: continue

        if 'vSphere' in ext:    # concatenate VSphere products
            ext_list = np.where(decode_df.Ext==ext, ext, '')
            for i in range(len(vsphere)):
                if not ext_list[i]: continue
                vsphere[i] = ext_list[i]
        else:
            export_df[ext] = np.where(decode_df.Ext==ext, ext, '')

    # split vsphere column to get version
    vsph_ver = [''] * len(decode_df)
    for i in range(len(vsph_ver)):
        if not vsphere[i]: continue
        ver = vsphere[i].split('-')[1].split('_')
        vsph_ver[i] = ''.join([ver[0], '.', ver[1]])
        vsphere[i] = 'vSphere'
        
    export_df["vSphere"] = vsphere
    export_df["vSp#"] = vsph_ver

    # include Extension and major/minor version numbers
    export_df["Extension"] = decode_df.Ext
    export_df["R"] = decode_df.R
    export_df["V"] = decode_df.V
    export_df["M"] = decode_df.M
    export_df["Type"] = decode_df.Type

    # download month and year
    export_df["DownloadMonth"] = decode_df.MonthYear.str.split('-').str[0]
    export_df["DownloadYear"] = decode_df.MonthYear.str.split('-').str[1]

    
    return export_df

    
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
    download_month = df.DownloadDate.dt.strftime("%b-%Y")
    df = df.assign(DownloadMonth=download_month)

    # sort data by Download Date by File
    df.sort_values(['DownloadDate','DownloadFile'], ascending=True, inplace=True)
    
    if 'index' in df.columns:      # drop index column created by assign
        df.drop('index', axis=1, inplace=True)

    swdlog.info("Cleaned data: {}".format(len(df)))

    # extract file details to save to file 
    export_df = get_export_downloadfile(df[['DownloadFile', 'Product', 'DownloadMonth']])
    savefile = os.path.join(os.getcwd(), "swdout", "exportswd.csv")
    export_df.to_csv(savefile, sep=',')
    
    # create 'ReleaseNo' column from export_df R & V columns
    release = export_df.R.map(str) + "." + export_df.V.map(str) # + "." + export_df.M.map(str)
    df = df.assign(ReleaseNo=release) 
    
   
    return df
