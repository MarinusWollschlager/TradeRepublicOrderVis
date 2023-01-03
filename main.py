from pdf_parser import PdfParser, EtfOrder
from financial_data_scrapper import FinanceDataScraper
from etf_plotter import EtfPlotter
from datetime import date
import pandas as pd

if __name__ == "__main__":
    PDF_PATH = r"/home/marinus/Documents/test_alle"


    parser = PdfParser(PDF_PATH)


    parsed_orders_df = parser.order_sorted_df
    from_date = parser.date_oldest_order
    to_date = parser.date_recent_order
    isin_list = parser.all_isins

    scrapper = FinanceDataScraper()

    plotter = EtfPlotter(PDF_PATH, "blabla", (from_date, to_date))

    for isin in isin_list:
        subplot_config = {"SubplotTitle": scrapper.fetch_isin_name(isin),
         "invest_history": parser.get_invest_history_isin(isin),
         "hist_data": scrapper.fetch_historical_data_points(isin, from_date, to_date)}

        plotter.add_subplot(subplot_config)
        

    plotter.create_plot(add_summarize_block=True)
    





