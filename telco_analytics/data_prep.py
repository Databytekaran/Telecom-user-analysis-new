from pathlib import Path

import numpy as np
import pandas as pd


APP_COLUMNS = [
    "Social_Media",
    "Google",
    "Email",
    "Youtube",
    "Netflix",
    "Gaming",
    "Other",
]

_APPLICATION_LABELS = {
    "Social_Media": "Social Media",
    "Google": "Google",
    "Email": "Email",
    "Youtube": "Youtube",
    "Netflix": "Netflix",
    "Gaming": "Gaming",
    "Other": "Other",
}


def load_raw_data(path: str | Path) -> pd.DataFrame:
    """Load an existing CSV or Excel xDR file without modifying it."""
    data_path = Path(path)
    if not data_path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {data_path}")
    if data_path.suffix.lower() == ".csv":
        return pd.read_csv(data_path)
    if data_path.suffix.lower() in {".xlsx", ".xlsm"}:
        return pd.read_excel(data_path)
    raise ValueError(f"Unsupported raw data format: {data_path.suffix}")


def add_application_totals(data: pd.DataFrame) -> pd.DataFrame:
    """Add per-session DL+UL byte totals for each application."""
    result = data.copy()
    for app, label in _APPLICATION_LABELS.items():
        downlink = f"{label} DL (Bytes)"
        uplink = f"{label} UL (Bytes)"
        result[f"{app}_Total_Bytes"] = result[downlink].fillna(0) + result[uplink].fillna(0)
    return result


def build_user_overview(
    data: pd.DataFrame, user_col: str = "MSISDN/Number"
) -> pd.DataFrame:
    """Aggregate session count, duration, traffic, and app bytes per customer."""
    prepared = data if all(f"{app}_Total_Bytes" in data for app in APP_COLUMNS) else add_application_totals(data)
    aggregations = {
        "Session_Count": (user_col, "size"),
        "Total_Duration_ms": ("Dur. (ms)", "sum"),
        "Total_DL_Bytes": ("Total DL (Bytes)", "sum"),
        "Total_UL_Bytes": ("Total UL (Bytes)", "sum"),
    }
    aggregations.update(
        {f"{app}_Total_Bytes": (f"{app}_Total_Bytes", "sum") for app in APP_COLUMNS}
    )
    overview = prepared.groupby(user_col).agg(**aggregations)
    overview["Total_Data_Bytes"] = overview["Total_DL_Bytes"] + overview["Total_UL_Bytes"]
    return overview


def treat_missing_outliers(
    data: pd.DataFrame, numeric_cols: list[str] | None = None
) -> pd.DataFrame:
    """Replace numeric missing values and IQR outliers with their column mean."""
    result = data.copy()
    columns = numeric_cols or result.select_dtypes(include=np.number).columns.tolist()
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype(float)
        values = result[column]
        mean = values.mean()
        if pd.isna(mean):
            result[column] = values.fillna(0)
            continue
        lower = values.quantile(0.25)
        upper = values.quantile(0.75)
        spread = upper - lower
        outside = (values < lower - 1.5 * spread) | (values > upper + 1.5 * spread)
        result.loc[outside, column] = mean
        result[column] = result[column].fillna(mean)
    return result


def treat_missing_and_outliers(
    data: pd.DataFrame, numeric_cols: list[str] | None = None
) -> pd.DataFrame:
    """Compatibility name retained for the existing notebook's function call."""
    return treat_missing_outliers(data, numeric_cols=numeric_cols)


def build_experience_table(
    data: pd.DataFrame, user_col: str = "MSISDN/Number"
) -> pd.DataFrame:
    """Aggregate average network experience and most frequent handset per customer."""
    prepared = data.copy()
    metric_columns = {
        "_tcp": ("TCP DL Retrans. Vol (Bytes)", "TCP UL Retrans. Vol (Bytes)"),
        "_rtt": ("Avg RTT DL (ms)", "Avg RTT UL (ms)"),
        "_throughput": ("Avg Bearer TP DL (kbps)", "Avg Bearer TP UL (kbps)"),
    }
    for metric, (downlink, uplink) in metric_columns.items():
        prepared[metric] = prepared[[downlink, uplink]].mean(axis=1)
    experience = prepared.groupby(user_col).agg(
        Avg_TCP_Retrans=("_tcp", "mean"),
        Avg_RTT=("_rtt", "mean"),
        Avg_Throughput=("_throughput", "mean"),
    )
    experience["Handset_Type"] = prepared.groupby(user_col)["Handset Type"].agg(
        lambda values: values.mode().iloc[0] if not values.mode().empty else np.nan
    )
    treated = treat_missing_outliers(
        experience,
        numeric_cols=["Avg_TCP_Retrans", "Avg_RTT", "Avg_Throughput"],
    )
    treated["Handset_Type"] = experience["Handset_Type"].fillna("Unknown")
    return treated