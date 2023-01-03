import pandas as pd
from typing import List
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, date
from matplotlib.ticker import FormatStrFormatter, MultipleLocator

class PlotObject:
    def __init__(self, title: str, data_source: pd.DataFrame, isin: List[str]):
        self.title = title
        self.data_source = data_source
        self.isin = isin

    def get_y(self):
        return list(self.data_source.index)

    def get_buy_in(self):
        col_names_buy_in = [isin+"_buy_in" for isin in self.isin]
        col_names_amount = [isin+"_amount" for isin in self.isin]

        single_buy_in = {}
        for buy_in_col, amount_col in zip(col_names_buy_in, col_names_amount):
            single_buy_in[buy_in_col] = self.data_source[buy_in_col].multiply(self.data_source[amount_col])

        df = pd.DataFrame(single_buy_in)

        return df.sum(axis=1)

    def get_eod_value(self):
        col_names_eod_value = [isin+"_eod" for isin in self.isin]
        col_names_amount = [isin+"_amount" for isin in self.isin]

        single_buy_in = {}
        for buy_in_col, amount_col in zip(col_names_eod_value, col_names_amount):
            single_buy_in[buy_in_col] = self.data_source[buy_in_col].multiply(self.data_source[amount_col])

        df = pd.DataFrame(single_buy_in)

        return df.sum(axis=1)

    def get_formatting_config(self):

        return {"Title": self.title,
                "line_buy_in": "k-",
                "line_value": "g"}


def format_ax(ax: plt.axis) -> None:
    """formats an axis"""

    # set x mayor & minor ticks and labels
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(4, 7, 10)))

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))

    for label in ax.get_xticklabels(which='major'):
        label.set(rotation=90, horizontalalignment='center')

    # set y ticks
    ax.yaxis.set_major_locator(MultipleLocator(base=200))
    ax.yaxis.set_major_formatter(FormatStrFormatter("%d €"))

    # align axis to origin
    ax.set_xlim(left=date_list[0], right=date_list[-1])
    ax.set_ylim(bottom=0)

    # disable spines
    ax.spines.right.set_visible(False)
    ax.spines.top.set_visible(False)


fig, ax = plt.subplots(2, figsize=(8.27, 11.69), sharex=True)

base = datetime.today()

date_list = [base - timedelta(days=x) for x in range(365*2)][::-1]
y1 = [v for v in range(365*2)]
y2 = [v*2-100 for v in range(365*2)]

ax[0].stackplot(date_list, [y1, y2], baseline="zero")

# ax[0].plot(date_list, y1, c="k", alpha=.4)
# ax[0].plot(date_list, y2, c="g", alpha=.4)
#
# ax[0].fill_between(date_list, y1, y2, where=[v1>v2 for v1, v2 in zip(y1, y2)], color="g", alpha=.5)
# ax[0].fill_between(date_list, y1, y2, where=[v1<v2 for v1, v2 in zip(y1, y2)], color="r", alpha=.5)

format_ax(ax[0])

plt.show()