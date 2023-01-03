import dataclasses
from dataclasses import dataclass, field
from PyPDF2 import PdfReader
import os
from datetime import datetime
from typing import Optional
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path, PurePath
import re


class EtfOrder():
    #__slots__ = "is_single_order", "date", "isin", "share_quantity", "order_total", "price_per_share"

    def __init__(self, 
                    is_single_order: bool,
                    date: datetime.date,
                    isin: str,
                    share_quantity: float,
                    order_total: float):
        self.is_single_order = is_single_order
        self.date = date
        self.isin = isin
        self.share_quantity = share_quantity
        self.order_total = order_total
        self.price_per_share = self.calc_price_per_share()

    def calc_price_per_share(self):
        return self.order_total/self.share_quantity

    def __eq__(self, other):
        return all([self.date == other.date, self.isin == other.isin])

    def __hash__(self):
        return int(self.date.strftime("%Y%m%d") + str(ord(self.isin[5])) + str(ord(self.isin[7])) + str(ord(self.isin[9])))


@dataclass(frozen=True)
class EtfOrder5():
    is_single_order: bool
    date: datetime.date
    isin: str
    share_quantity: float
    order_total: float
    price_per_share: float

    # def __post_init__(self):
    #     self.price_per_share = self.order_total / self.share_quantity

    def __lt__(self, other):
        return self.date < other.date

    def __gt__(self, other):
        return self.date > other.date

    def __ge__(self, other):
        return self.date >= other.date

    def __le__(self, other):
        return self.date <= other.date

    def __eq__(self, other):
        return all([self.date == other.date, self.isin == other.isin])

    def __add__(self, other):
        return EtfOrder(True, self.date, self.isin, self.share_quantity + other.share_quantity, self.order_total + other.order_total, self.price_per_share + other.price_per_share)

    def __radd__(self, other):
        return EtfOrder(True, self.date, self.isin, self.share_quantity + other.share_quantity, self.order_total + other.order_total, self.price_per_share + other.price_per_share)


class PdfParser():
    def __init__(self, path_to_pdf: str) -> None:
        self._PATH_TO_PDF = self._validate_path_to_pdfs(path_to_pdf)
        self._list_of_pdfs = self.list_of_pdfs()
        self.order_list = self._parse_pdfs_2_order_list()
        self.order_sorted_df = self.order_list_2_df(self.order_list)

        self.date_oldest_order = self.order_sorted_df.index[0]
        self.date_recent_order = self.order_sorted_df.index[-1]
        self.all_isins = list(set(self.order_sorted_df["isin"]))

    def _parse_pdfs_2_order_list(self) -> list:
        """parses .pdf files into etf_order dataclasses"""

        def extract_pdf_elements(pdf_file_name: str, page: int = 0) -> list:
            """parse text elements from .pdf file into a list"""

            with open(self._PATH_TO_PDF.joinpath(pdf_file_name), "rb") as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                page_obj = pdf_reader.pages[page]
                pdf_text_elements = page_obj.extract_text().split("\n")

            return pdf_text_elements

        def extract_is_single_order() -> bool:
            """extract if order is from saving plan or single order"""

            if any(True for element in self._elements if "Market-Order" in element):
                return True
            elif any(True for element in self._elements if "Sparplanausführung" in element):
                return False

        def extract_execution_date() -> datetime.date:
            """extract execution date from order"""

            concat_lines = " ".join([self._elements[18], self._elements[19]])
            phrases_list = concat_lines.split(" ")

            for phrase in phrases_list:
                try:
                    execution_date_str = datetime.strptime(phrase[:10], "%d.%m.%Y")
                except ValueError:
                    continue

            return execution_date_str

        def extract_isin(row_index: int) -> str:
            """extract ISIN"""

            splitted_elements = self._elements[row_index].split(" ")
            return splitted_elements[1][:12]

        def extract_share_quantity(row_index: int) -> float:
            """extract share quantity"""

            str_containing_share_quantity = self._elements[row_index].split(" ")[1]
            share_quantity = str_containing_share_quantity[12:].replace(",", ".")
            return float(share_quantity)

        def extract_order_total(row_index: int) -> float:
            """extract full amount of order"""

            str_containing_order_total = self._elements[row_index].split(" ")[5]
            order_total = str_containing_order_total.replace(",", ".")
            return float(order_total)

        def calc_price_per_share(share_quantity: float = 0, order_total: float = 0) -> float:
            return order_total/share_quantity

        def get_relevant_row_index_with_purchase_infos() -> int:
            """
            returns the index within self._elements, 
            which contains infos about:
            - share_quantity
            - isin
            - order_total

            Due to inconsistent pdf layouts, the index varies.
            """

            lines_contain_isin = [True if "ISIN:" in element else False for element in self._elements]

            return lines_contain_isin.index(True)

        self._order_list = []
        for pdf in tqdm(self._list_of_pdfs):
            self._elements = extract_pdf_elements(pdf)
            row_index = get_relevant_row_index_with_purchase_infos()

            share_quantity = extract_share_quantity(row_index)
            order_total = extract_order_total(row_index)
            price_per_share = calc_price_per_share(share_quantity, order_total)

            self._order_list.append(EtfOrder(extract_is_single_order(),
                                    extract_execution_date(),
                                    extract_isin(row_index),
                                    share_quantity,
                                    order_total))

        return self._order_list

    def _agg_same_day_orders(self) -> list:
        """aggregates orders in list, which are executed for same isin and on same day and deletes single ones"""

        seen = set()
        dups = []

        for order in self.order_list:
            if order in seen:
                dups.append(order)
            else:
                seen.add(order)

        to_delete = []
        for order_profile in dups:
            idx_to_agg = [idx for idx, _ in enumerate(self.order_list) if _ == order_profile]
            to_delete.extend(idx_to_agg)


            self.order_list.append(EtfOrder(is_single_order=True,
                                            date=self.order_list[idx_to_agg[0]].date,
                                            isin=self.order_list[idx_to_agg[0]].isin,
                                            share_quantity=sum([order.share_quantity for i, order in enumerate(self.order_list) if i in idx_to_agg]),
                                            order_total=sum([order.order_total for i, order in enumerate(self.order_list) if i in idx_to_agg])))


        for idx in sorted(to_delete, reverse=True):
            del self.order_list[idx]

    def order_list_2_df(self, order_list: list) -> pd.DataFrame:
        """parses list of etf_order instances into pandas dataframe"""

        if not all([isinstance(order, EtfOrder) for order in self.order_list]):
            raise Exception("order_list does not contain elements of dataclass etf_order")

        else:

            self._agg_same_day_orders()

            self._order_list.sort(key = lambda order: order.date)

            df = pd.DataFrame([order.__dict__ for order in self.order_list])

            df.set_index(["date"], inplace=True)

            return df

    def get_invest_history_isin(self, isin: str) -> pd.DataFrame:
        """filters parsed orders on isin and returns df with invest history on daily granularity (explorated)"""

        df = pd.DataFrame(index=pd.date_range(start=self.date_oldest_order, end=self.date_recent_order))
        order_sorted_df_isin = self.order_sorted_df.loc[self.order_sorted_df["isin"]==isin].copy()

        order_sorted_df_isin["acc_shares"] = order_sorted_df_isin["share_quantity"].cumsum()

        order_sorted_df_isin["buy_in"] = order_sorted_df_isin["order_total"].cumsum() / order_sorted_df_isin["acc_shares"]

        df_joined = df.join(other=order_sorted_df_isin).fillna(method="ffill")

        return df_joined.loc[:, ["acc_shares", "buy_in"]]

    def _validate_path_to_pdfs(self, path_to_pdf: str):
        """valdiates if path_to_pdf exists"""

        PATH_TO_PDF = Path(path_to_pdf)

        if PATH_TO_PDF.exists():
            return PATH_TO_PDF
        else:
            raise Exception("path_to_pdf does not exists")

    def list_of_pdfs(self):
        """returns a list with .pdf files within self._PATH_TO_PDF object"""

        pdf_name_list = [pdf_name.name for pdf_name in self._PATH_TO_PDF.iterdir() if pdf_name.name.endswith(".pdf")]

        if pdf_name_list:
            return pdf_name_list
        else:
            raise Exception("no pdfs in path found")










