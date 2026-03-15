import pandas as pd
from pathlib import Path

# List of years for which we want to load survey data.
YEARS = [2022, 2023, 2024]

# Resolve project root so this notebook works whether CWD is repo root or notebooks/.
CANDIDATE_ROOTS = [Path.cwd(), Path.cwd().parent]
PROJECT_ROOT = next(
    (p for p in CANDIDATE_ROOTS if (p / "data" / "raw").exists()), Path.cwd()
)
RAW_DIR = PROJECT_ROOT / "data" / "raw"
print(f"Working directory: {Path.cwd()}")
print(f"Using RAW_DIR: {RAW_DIR}")

# STEP 1: LOAD DATA

# Initialize an empty list to hold DataFrames for each year.
frames = []

# Iterate through each year, read the corresponding CSV file, and append to the list.
for year in YEARS:
    path = RAW_DIR / str(year) / "survey_results_public.csv"

    # Check if file path exists. If not, raise FileNotFoundError
    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}. Run scripts/acquire.sh first to download/extract data."
        )

    # Read the CSV file into a DataFrame
    df = pd.read_csv(path, low_memory=False)
    df["survey_year"] = year  # Add new column 'year' set to its year
    frames.append(
        df
    )  # Append the DataFrame to the list of frames for later concatenation.

df_raw = pd.concat(frames, ignore_index=True)

# STEP 2: CLEAN DATA

# Drop rows with no salary (can't train without a target)
df = df_raw.dropna(subset=["ConvertedCompYearly"]).copy()

# Remove outliers (informed by your Step 2 inspection above)
df = df[df["ConvertedCompYearly"].between(10_000, 400_000)]

# Convert YearsCodePro to numeric robustly (works for mapped labels and numeric-like strings)
YCP_MAP = {
    "Less than 1 year": 0.5,
    "More than 50 years": 52.0,
}

# Keep known labels from map; parse everything else by extracting digits
ycp_raw = df["YearsCodePro"]
ycp_mapped = ycp_raw.map(YCP_MAP)
ycp_parsed = pd.to_numeric(
    ycp_raw.astype("string").str.extract(r"(\d+)", expand=False),
    errors="coerce",
)

df["YearsCodePro"] = ycp_mapped.fillna(ycp_parsed).astype(float)

# Encode multi-select columns
lang_dummies = df["LanguageHaveWorkedWith"].str.get_dummies(sep=";")
top20_langs = lang_dummies.sum().nlargest(20).index
df = pd.concat([df, lang_dummies[top20_langs].add_prefix("lang_")], axis=1)

#  One-hot encode single-select categoricals
df = pd.get_dummies(df, columns=["RemoteWork", "EdLevel", "Employment"], dummy_na=False)

# Standardise Country
country_counts = df["Country"].value_counts()
rare_countries = country_counts[country_counts < 100].index
df["Country"] = df["Country"].replace(rare_countries, "Other")

# Save
out = Path("data/clean")
out.mkdir(exist_ok=True)
df.to_csv(out / "survey_clean.csv", index=False)
print(f"\nSaved {len(df):,} rows, {df.shape[1]} cols → data/clean/survey_clean.csv")
