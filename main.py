#!/usr/bin/python3

"""********************************************************************
Created by:   Fiona Egbulefu (Contractor)

Created date: 10 June 2019

Description:  Main script to automate KPI charts for 'Software Downloads'
              - Calls module to import raw data
              - Calls module to build charts

********************************************************************"""

import os
import sys

try:
    import pandas as pd
    import warnings
    
except ImportError as e:
    print("Import error: {}".format(str(e)))
    sys.exit(-1)

# user defined modules
import util
import plotswd
import prepswd


# ------
# Setup
# ------

swdlog = util.setup_logger("swdlog", "swdlog.log")

swdfile = r'data\SWDL_data.xlsx'
swdsheet = r'SWDownloads-123'           

products = {'CMS': 'Server', 'CMA': 'Client', 'CMM': 'Management'}


#-------------------------------------------------------------
# Import data from a defined sheet in a given Excel workbook
# - returns DataFrame structure 
#-------------------------------------------------------------
def import_from_excel(xlfile, xlsheet):

    import_df = None

    if not xlfile or not xlsheet:
        swdlog.error("Excel filename and sheetname required for import")
        return import_df
    
    try:
    
        # import Excel data from specific workbook and sheet; ignore xlrd warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            import_df = pd.read_excel(xlfile, xlsheet)
            
    except Exception as e:
        swdlog.error("Exception: {}".format(str(e)))


    if not import_df is None:
        swdlog.info("Imported records: {}".format(len(import_df)))

    return import_df


#-------------------------------------------------------------
# Get data for downloads
# - returns Dataframe structure
#-------------------------------------------------------------
def main():

    xlfile = os.path.join(os.getcwd(), swdfile)

    # import data
    import_df = import_from_excel(xlfile, swdsheet)
    if import_df is None:
        swdlog.warning("No download data available!")
        return

    swd_df = prepswd.filter_downloads(import_df)
    
    #=============================
    # Plot KPIs for all Products
    #=============================

    for period in ['18M', '6M', '6W', '6D', 'allW']:

        df_plot = prepswd.group_data_by_date(swd_df, period)
    
        swdlog.info("Plot KPI: All products for period {0}".format(period))

        # plot kpi as single/stacked bars
        if period in ['18M', '6D', '6W', 'allW']:
            kpi_chart = plotswd.plot_stacked_chart(df_plot[['CMS','CMA','CMM']], "allStacked", period)
        else:
            kpi_chart = plotswd.plot_bar_chart(df_plot[['CMS','CMA','CMM']], "allBars", period)

        if kpi_chart:
            swdlog.info("Chart created for all products: {0}".format(kpi_chart))


    #========================
    # Plot kpis for CMS 
    #========================

    # filter data for 'CMS'
    product_filter = swd_df.apply(lambda x: x.Product == 'CMS', axis=1)     
    df_product = swd_df[product_filter]

    if len(df_product) == 0:
        swdlog.warning("No data found for 'CMS'".format(pcode))
        return 

    for period in ['18M', '6M', '6W', '6D', 'allW']:
        
        df_plot = prepswd.group_data_by_date(df_product, period, True)
        
        # plot kpi as single/stacked bars
        if period in ['18M', '6D', '6W', 'allW']:
            kpi_chart = plotswd.plot_stacked_chart(df_plot, "CMSStacked", period)
        else:
            kpi_chart = plotswd.plot_bar_chart(df_plot, "CMSBars", period)

        if kpi_chart:
            swdlog.info("Chart created for all products: {0}".format(kpi_chart))
                        

    return



#***********#
# M A I N   #
#***********#

if __name__ == "__main__":
    
    swdlog.info("Start Software Downloads automation.......")

    main()

    swdlog.info("Finished!")
    
