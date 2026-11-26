
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

GOLD_FILE = Path("data/gold/country_indicators.parquet")


def load_data():
    print("Loading Gold dataset...")

    df = pd.read_parquet(GOLD_FILE)

    print(f"Dataset loaded: {len(df):,} rows")

    return df


def analyze_missing_values(df):
    print("\nMissing values analysis:")

    missing = df.isnull().sum()

    missing_percentage = (
        df.isnull().mean() * 100
    ).round(2)

    report = pd.DataFrame({
        "missing_values": missing,
        "missing_percentage": missing_percentage
    })

    print(report[report["missing_values"] > 0])


def main():
    df = load_data()

    print("\nDataset dimensions:")
    print(df.shape)

    print("\nData types:")
    print(df.dtypes)

    print("\nDescriptive statistics:")
    print(df.describe())

    print("\nMissing values:")
    print(df.isnull().sum())

    analyze_missing_values(df)
    identify_missing_countries(df)
    analyze_by_continent(df)
    analyze_top_countries(df)
    analyze_top_countries_per_capita(df)
    plot_top_10_deaths(df)


def identify_missing_countries(df):
    print("\nCountries with missing values:")

    missing_countries = df.loc[
        df.isnull().any(axis=1),
        [
            "country",
            "continent",
            "total_cases",
            "total_deaths",
            "population",
            "fatality_rate"
        ]
    ]

    print(missing_countries.to_string(index=False))

    print(
        f"\nTotal countries with missing values: "
        f"{len(missing_countries)}"
    )


def analyze_by_continent(df):
    print("\nCOVID-19 indicators by continent:")

    continent_summary = (
        df.groupby("continent")
        .agg(
            countries=("country", "count"),
            total_cases=("total_cases", "sum"),
            total_deaths=("total_deaths", "sum"),
            avg_cases_per_million=("cases_per_million", "mean"),
            avg_deaths_per_million=("deaths_per_million", "mean"),
            avg_fatality_rate=("fatality_rate", "mean")
        )
        .sort_values("total_cases", ascending=False)
        .round(2)
    )

    print(continent_summary.to_string())


def analyze_top_countries(df):
    columns = [
        "country",
        "continent",
        "total_cases",
        "total_deaths",
        "cases_per_million",
        "deaths_per_million"
    ]

    print("\nTop 10 countries by total cases:")

    top_cases = (
        df.dropna(subset=["total_cases"])
        .sort_values("total_cases", ascending=False)
        [columns]
        .head(10)
    )

    print(top_cases.to_string(index=False))

    print("\nTop 10 countries by total deaths:")

    top_deaths = (
        df.dropna(subset=["total_deaths"])
        .sort_values("total_deaths", ascending=False)
        [columns]
        .head(10)
    )

    print(top_deaths.to_string(index=False))


def analyze_top_countries_per_capita(df):
    print("\nTop 10 countries by deaths per million:")

    top_deaths = (
        df.dropna(subset=["deaths_per_million"])
        .sort_values(
            "deaths_per_million",
            ascending=False
        )
        [["country", "continent", "deaths_per_million"]]
        .head(10)
    )

    print(top_deaths.to_string(index=False))

    print("\nTop 10 countries by cases per million:")

    top_cases = (
        df.dropna(subset=["cases_per_million"])
        .sort_values(
            "cases_per_million",
            ascending=False
        )
        [["country", "continent", "cases_per_million"]]
        .head(10)
    )

    print(top_cases.to_string(index=False))



def plot_top_10_deaths(df):
    print("\nGenerating professional deaths chart...")

    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    top_deaths = (
        df.dropna(subset=["total_deaths"])
        .nlargest(10, "total_deaths")
        .sort_values("total_deaths")
    )

    fig, ax = plt.subplots(figsize=(13, 8))

    # Highlight Brazil and keep other countries neutral
    colors = [
        "#16A6A1" if country == "Brazil" else "#294C70"
        for country in top_deaths["country"]
    ]

    bars = ax.barh(
        top_deaths["country"],
        top_deaths["total_deaths"],
        color=colors,
        height=0.65
    )

    # Chart title and subtitle
    fig.suptitle(
        "COVID-19 | Top 10 Countries by Deaths",
        fontsize=19,
        fontweight="bold",
        x=0.12,
        ha="left"
    )

    ax.set_title(
        "Cumulative reported deaths by country",
        fontsize=11,
        color="#64748B",
        loc="left",
        pad=18
    )

    # Format values on bars
    max_value = top_deaths["total_deaths"].max()

    for bar in bars:
        value = bar.get_width()

        ax.text(
            value + max_value * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.0f}",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#334155"
        )

    # Axis formatting
    ax.set_xlim(0, max_value * 1.20)
    ax.set_xlabel("Total reported deaths", fontsize=11, labelpad=12)
    ax.set_ylabel("")

    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:,.0f}")
    )

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.25
    )

    ax.set_axisbelow(True)

    # Remove unnecessary borders
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color("#CBD5E1")

    ax.tick_params(axis="y", length=0, labelsize=11)
    ax.tick_params(axis="x", labelsize=9, colors="#64748B")

    # Source information
    fig.text(
        0.12,
        0.025,
        "Source: Our World in Data | COVID-19 dataset",
        fontsize=9,
        color="#64748B"
    )

    fig.text(
        0.88,
        0.025,
        "Data Engineering Project",
        fontsize=9,
        color="#64748B",
        ha="right"
    )

    fig.subplots_adjust(
        left=0.12,
        right=0.91,
        top=0.84,
        bottom=0.12
    )

    output_file = output_dir / "top_10_deaths.png"

    fig.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close(fig)

    print(f"Chart saved: {output_file}")




if __name__ == "__main__":
    main()
