import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from typing import List
import matplotlib.dates as mdates
from matplotlib.ticker import FormatStrFormatter, MultipleLocator

class SubPlotObjectSingle:
    def __init__(self, subplot_config: dict):
        self.title = subplot_config["SubplotTitle"]
        self._invest_history = subplot_config["invest_history"]
        self._hist_data = subplot_config["hist_data"]

    def get_y(self):
        return list(self._invest_history.index)

    def get_buy_in(self):
        return self._invest_history["acc_shares"] * self._invest_history["buy_in"]

    def get_eod_values(self):
        return self._invest_history["acc_shares"] * self._hist_data

class SubPlotObjectMultiple:
    def __init__(self, subplot_config_list: list):
        self._subplot_config_list = subplot_config_list
        self._buy_in_list = [_SubPlotObjectSingle.get_buy_in() for _SubPlotObjectSingle in self._subplot_config_list]
        self._eod_values = [_SubPlotObjectSingle.get_eod_values() for _SubPlotObjectSingle in self._subplot_config_list]

    def get_buy_in(self):
        return pd.concat(self._buy_in_list, axis=1).sum(axis=1)

    def get_eod_values(self):
        return pd.concat(self._eod_values, axis=1).sum(axis=1)

class EtfPlotter():
    def __init__(self, path_to_safe: Path, file_name: str, plot_time_range: tuple):
        self._PATH_TO_SAFE = path_to_safe
        self._FILE_NAME = file_name
        self._plot_time_range = plot_time_range

        self._subplot_object_list = []

    def add_subplot(self, subplot_config: dict) -> None:
        """creates subplot object and appends it to the list to plot"""

        self._subplot_object_list.append(SubPlotObjectSingle(subplot_config))

    def _format_ax(self, ax: plt.axis) -> None:
        """formats an axis"""

        # set x mayor & minor ticks and labels
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(4, 7, 10)))

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))

        for label in ax.get_xticklabels(which='major'):
            label.set(rotation=90, horizontalalignment='center')

        # set y ticks
        ax.yaxis.set_major_locator(MultipleLocator(base=1000))
        ax.yaxis.set_minor_locator(MultipleLocator(base=200))
        ax.yaxis.set_major_formatter(FormatStrFormatter("%d €"))

        # add v lines to major ticks
        for label in ax.get_yticklabels(which="major")[1:]:
            ax.axhline(label.get_position()[1], color="dimgrey", alpha=.3, zorder=1, linewidth=.8)

        for label in ax.get_yticklabels(which="minor")[1:]:
            ax.axhline(label.get_position()[1], color="silver", alpha=.3, zorder=1, linewidth=.3)
        
        # align axis to origin
        ax.set_xlim(left=self._plot_time_range[0], right=self._plot_time_range[1])
        ax.set_ylim(bottom=0)

        # disable spines
        ax.spines.right.set_visible(False)
        ax.spines.top.set_visible(False)

    def create_plot(self, add_summarize_block=True):
        """creates a plot out of SubPlotObjects and saves the plot as pdf"""

        if not add_summarize_block:
            fig, ax = plt.subplots(len(self._subplot_object_list), figsize=(8.2, 11.6), sharex=True)
        else:
            fig, ax = plt.subplots(len(self._subplot_object_list) + 1, figsize=(8.2, 11.6), sharex=True)

        for idx, sub_plot_object in enumerate(self._subplot_object_list):
            ax[idx].plot(sub_plot_object.get_eod_values(), c="g", linewidth=1, label="EoD value", zorder=2)
            ax[idx].plot(sub_plot_object.get_buy_in(), c="k", linewidth=1, label="Buy in", zorder=2)
            ax[idx].set_title(sub_plot_object.title, loc="left", fontsize=8)
            ax[idx].legend(loc="upper left", fontsize=8)

        if add_summarize_block:
            ob = SubPlotObjectMultiple(self._subplot_object_list)
            ax[-1].plot(ob.get_eod_values(), c="g", linewidth=1, label="EoD value", zorder=2)
            ax[-1].plot(ob.get_buy_in(), c="k", linewidth=1, label="Buy in", zorder=2)
            ax[-1].set_title("Overview", loc="left", fontsize=8)
            ax[-1].legend(loc="upper left", fontsize=8)


        for axis in ax:
            self._format_ax(axis)

        fig.tight_layout()
        plt.savefig(f"{self._FILE_NAME}.pdf", bbox_inches="tight")

