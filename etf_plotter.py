import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, field


class SubPlotObject():
    def __init__(self, isin: str, isin_name: str, historical_data_df: pd.DataFrame, orders_df: pd.DataFrame):
        self._isin = isin
        self.isin_name = isin_name
        self._historical_data = historical_data_df
        self._orders_df = orders_df
        self._orders_isin = self._orders_df.loc[self._orders_df["isin"] == self._isin, [f"{self._isin}_buy_in", f"{self._isin}_count"]]
        self._merged_df_isin = self._historical_data.merge(self._orders_isin, how="left", left_index=True, right_index=True)
        self._merged_df_isin.fillna(method="ffill", inplace=True)

        self.isin_value_per_day = self._calculate_isin_value_per_day()
        self.isin_buy_in_per_day = self._calculate_isin_buy_in()

        self.loss_profit_per_day = self._get_loss_profit_per_day()

    def _calculate_isin_value_per_day(self) -> pd.Series:
        """calculate the value of the currently owned shares"""

        return self._merged_df_isin[f"{self._isin}_count"] * self._merged_df_isin["close_rate"]

    def _calculate_isin_buy_in(self) -> pd.Series:
        """calculate the buy in * count per day"""
    
        return self._merged_df_isin[f"{self._isin}_count"] * self._merged_df_isin[f"{self._isin}_buy_in"]

    def _get_loss_profit_per_day(self) -> pd.Series:
        """calculate the current loss or profit per day"""

        return self.isin_value_per_day - self.isin_buy_in_per_day


class EtfPlotter():
    def __init__(self, path_to_safe: Path, file_name: str, parsed_orders: pd.DataFrame, plot_time_range: tuple):
        self._PATH_TO_SAFE = path_to_safe
        self._FILE_NAME = file_name
        self._parsed_orders = parsed_orders
        self._plot_time_range = plot_time_range

        self._subplot_object_list = []

    def add_subplot(self, isin: str, isin_name: str, historical_data: pd.DataFrame) -> None:
        """creates subplot object and appends it to the list to plot"""

        self._subplot_object_list.append(SubPlotObject(isin, isin_name, historical_data, self._parsed_orders))

    def format_plot(self, list_of_axes: []) -> None:
        """
        formats the whole block:
        - shared x
        - quarterly tick labels
        - legend in each subplot
        - title in each block
        """

        for ax in list_of_axes:
            ax.legend(loc="upper left", frameon=False)
            ax.set_title()



    def create_plot(self, add_summarize_block=True):
        """creates a plot out of SubPlotObjects and saves the plot as pdf"""

        fig, ax = plt.subplots(len(self._subplot_object_list) + 1, figsize=(8.2, 11.6))

        list_isin_value_per_day = []
        list_isin_buy_in_per_day = []
        for idx, sub_plot_object in enumerate(self._subplot_object_list):
            ax[idx].plot(sub_plot_object.isin_value_per_day, c="k", label="Value")
            ax[idx].plot(sub_plot_object.isin_buy_in_per_day, c="g", label="Buy in")
            ax[idx].set_xlim(left=self._plot_time_range[0], right=self._plot_time_range[1])

            # self._ax[idx].legend(loc="upper left")
            ax[idx].set_title(sub_plot_object.isin_name)


        self.format_plot(ax)

            # if add_summarize_block:
            #     list_isin_value_per_day.append(sub_plot_object.isin_value_per_day)
            #     list_isin_buy_in_per_day.append(sub_plot_object.isin_buy_in_per_day)

        # if add_summarize_block:
        #     self._ax[-1].plot(pd.concat(list_isin_value_per_day, axis=1).sum(axis=1), c="k")
        #     self._ax[-1].plot(pd.concat(list_isin_buy_in_per_day, axis=1).sum(axis=1), c="k")
            
        #     self._ax[-1].plot(pd.DataFrame({idx: pd_series for idx, pd_series in enumerate(list_isin_value_per_day)}).sum(axis=1), c="k")
        #     self._ax[-1].plot(pd.DataFrame({idx: pd_series for idx, pd_series in enumerate(list_isin_buy_in_per_day)}).sum(axis=1), c="g")


        fig.tight_layout()
        plt.savefig(f"{self._FILE_NAME}.pdf", bbox_inches="tight")

