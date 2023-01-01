from pdf_parser import PdfParser, EtfOrder
from financial_data_scrapper import FinanceDataScraper
from etf_plotter import EtfPlotter
from datetime import date


if __name__ == "__main__":
    PDF_PATH = r"/home/marinus/Documents/test_alle"


    parser = PdfParser(PDF_PATH)


    parsed_orders_df = parser.order_sorted_df
    from_date = parser.date_oldest_order
    to_date = parser.date_recent_order
    isin_list = parser.all_isins

    plotter = EtfPlotter(PDF_PATH, "blabla", parsed_orders_df, (from_date, to_date))

    scrapper = FinanceDataScraper()

    for isin in isin_list:
    	historical_data = scrapper.fetch_historical_data_points(isin, from_date, to_date)
    	# isin_name = scrapper.fetch_isin_name(isin)
    	isin_name = "Testname"
    	plotter.add_subplot(isin, isin_name, historical_data)
    
    plotter.create_plot(add_summarize_block=False)




