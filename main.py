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
import plotswdl
import prepswdl


# --------- #
# Constants #
# --------- #

PRODUCTS = {"CMS": "Cisco Meeting Server", "CMA": "Cisco Meeting App", "CMM": "Cisco Meeting Manager"}

SWDLFILE = r'data\SWDL_data.xlsx'
SWDLSHEET = r'SWDownloads-123'           

# setup log
swdllog = util.setup_logger("swdllog", "swdllog.log")



#-------------------------------------------------------------
# Import data from a defined sheet in a given Excel workbook
# - returns DataFrame structure 
#-------------------------------------------------------------
def import_from_excel(xlfile, xlsheet):

    import_df = None

    if not xlfile or not xlsheet:
        swdllog.error("Excel filename and sheetname required for import")
        return import_df
    
    try:
    
        # import Excel data from specific workbook and sheet; ignore xlrd warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            import_df = pd.read_excel(xlfile, xlsheet)
            
    except Exception as e:
        swdllog.error("Exception: {}".format(str(e)))


    if not import_df is None:
        swdllog.info("Imported records: {}".format(len(import_df)))

    return import_df


#-------------------------------------------------------------
# Get data for downloads
# - returns Dataframe structure
#-------------------------------------------------------------
def main():

    xlfile = os.path.join(os.getcwd(), SWDLFILE)

    # import data
    import_df = import_from_excel(xlfile, SWDLSHEET)
    if import_df is None:
        swdllog.warning("No download data available!")
        return

    swdl_df = prepswdl.filter_downloads(import_df)
    
    #=============================
    # Plot KPIs for all Products
    #=============================

    for period in ['18M', '6M', '6W', '6D', 'allW']:
       
        df_plot = prepswdl.group_data_by_date(swdl_df, period)
    
        swdllog.info("Plot KPI: All products for period {0}".format(period))

        # plot kpi as single/stacked bars
        if period in ['18M', '6D', '6W', 'allW']:
            kpi_chart = plotswdl.plot_stacked_chart(df_plot[['CMS','CMA','CMM']], "allProducts", period)
        else:
            kpi_chart = plotswdl.plot_bar_chart(df_plot[['CMS','CMA','CMM']], "allProducts", period)

        if kpi_chart:
            swdllog.info("Chart created for all products: {0}".format(kpi_chart))


    #========================
    # Plot kpis by Product 
    #========================

    for product in PRODUCTS:
        
        # filter data by product
        pfilter = swdl_df.apply(lambda x: x.Product == product, axis=1)     
        df_product = swdl_df[pfilter]

        if len(df_product) == 0:
            swdllog.warning("No data found for {}".format(PRODUCTS[product]))
            continue 

        for period in ['12W', '18M', 'allW']:
           
            df_plot = prepswdl.group_data_by_date(df_product, period, product)
  
            kpi_chart = plotswdl.plot_stacked_chart(df_plot, product, period)
            if kpi_chart:
                swdllog.info("Chart created for {0} {1}: {2}".format(product, period, kpi_chart))
                        

    return



#***********#
# M A I N   #
#***********#

if __name__ == "__main__":
    
    swdllog.info("Start Software Downloads automation.......")

    main()

    swdllog.info("Finished!")
    
