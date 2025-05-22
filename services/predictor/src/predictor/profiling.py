import pandas as pd
from ydata_profiling import ProfileReport


def profile_data(data: pd.DataFrame, output_file: str):
    """
    Profile the data and save the report to the given file.
    Generates a HTML file containing the EDA report.

    Args:
        data: The data to profile.
        output_file: The file to save the report to.
    """
    profile = ProfileReport(
        data,
        tsmode=True,
        sortby='window_start_ms',
        title='Data Profiling Report',
    )
    profile.to_file(output_file)
