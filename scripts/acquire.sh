#!/usr/bin/env bash

# This script downloads the Stack Overflow Developer Survey datasets for the specified years,
# extracts the relevant CSV files, and performs a basic integrity check by counting rows and columns.

set -euo pipefail # Exit on error, treat unset variables as errors, and prevent errors in pipelines from being masked.

# Define the base URL and the years we want to download
BASE="https://survey.stackoverflow.co/datasets/stack-overflow-developer-survey"
YEARS=(2022 2023 2024)

# Create the raw data directory if it doesn't exist
mkdir -p data/raw

# Loop through each year, download the ZIP file, extract the relevant CSVs, and perform an integrity check
for YEAR in "${YEARS[@]}"; do
    # Inform the user about the current download
    echo "=== Downloading $YEAR ==="
    
    # Download the ZIP. -f makes HTTP errors fail; retries help with transient network issues.
    TMP_ZIP="data/raw/survey_${YEAR}.zip.tmp" # Use a temporary file to avoid leaving a corrupted ZIP if the download fails
    OUT_ZIP="data/raw/survey_${YEAR}.zip" # Final ZIP file path after successful download and validation
    
    # The --retry-connrefused option allows curl to retry even if the connection is refused, which can be helpful if the server is temporarily unavailable.
    curl -fL --retry 3 --retry-delay 2 --retry-connrefused \
        "${BASE}-${YEAR}.zip" -o "${TMP_ZIP}"

    # Basic sanity check before replacing the final file.
    if [[ ! -s "${TMP_ZIP}" ]]; then
        echo "Download failed for $YEAR: empty file received"
        rm -f "${TMP_ZIP}"
        exit 1
    fi

    # Validate archive structure so unzip errors are caught early and clearly.
    unzip -t "${TMP_ZIP}" >/dev/null
    mv -f "${TMP_ZIP}" "${OUT_ZIP}"
    
    # Extract only the files we need — skip the PDF
    # The -o flag in unzip allows us to overwrite existing files without prompting, which is useful for repeated runs.
    # The -d flag specifies the target directory for extraction, which is organized by year.
    # Note: The exact file names in the ZIP may vary, so we use a wildcard to match the expected CSV files.
    # If the ZIP structure changes, you may need to adjust the file paths in the unzip command.
    # The unzip command will extract the specified CSV files into the "data/raw/${YEAR}/" directory, creating it if it doesn't exist.
    unzip -o "${OUT_ZIP}" \
        "survey_results_public.csv" \
        "survey_results_schema.csv" \
        -d "data/raw/${YEAR}/"
    
    # Integrity check
    ROWS=$(wc -l < "data/raw/${YEAR}/survey_results_public.csv") # Count lines to get the number of rows (including header)
    COLS=$(head -1 "data/raw/${YEAR}/survey_results_public.csv" | tr ',' '\n' | wc -l) # Count columns by taking the header line, replacing commas with newlines, and counting lines
    echo "  Year $YEAR: $ROWS rows, $COLS columns" # Output the integrity check results for the current year
    
    # Keep the ZIP for reproducibility, or delete to save space:
    # rm "data/raw/survey_${YEAR}.zip"
done

# Final message to indicate all downloads and checks are complete
echo "=== All downloads complete ==="