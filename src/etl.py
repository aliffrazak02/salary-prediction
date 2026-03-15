import pandas as pd
from pathlib import Path

# List of years for which we want to load survey data.
YEARS = [2022, 2023, 2024]

# Resolve project root so this notebook works whether CWD is repo root or notebooks/.
CANDIDATE_ROOTS = [Path.cwd(), Path.cwd().parent]
PROJECT_ROOT = next((p for p in CANDIDATE_ROOTS if (p / "data" / "raw").exists()), Path.cwd())
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
    df["survey_year"] = year # Add new column 'year' set to its year
    frames.append(df)        # Append the DataFrame to the list of frames for later concatenation.
    
    # Print the number of rows and columns for each year's DataFrame 
    print(f"{year}: {len(df):,} rows, {df.shape[1]} cols") 
    
df_raw = pd.concat(frames, ignore_index=True)

# STEP 2: CLEAN DATA
