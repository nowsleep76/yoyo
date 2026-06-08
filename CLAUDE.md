# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a work tool for Home & Shopping (홈앤쇼핑) employees that generates stock market analysis charts.

**Key Requirements:**
- All UI text, labels, and guidance must be in **Korean** (한국어)
- Currency amounts must be formatted in **Korean won (₩) with thousand separators** (e.g., `341,000원`)
- Current implementation fetches Samsung Electronics stock data and generates a 6-month historical chart

## Running the Script

**Prerequisites:**
- Python 3.7+
- Install dependencies: `pip install pykrx matplotlib pandas requests`

**Execute the script:**
```bash
python samsung_chart.py
```

Output:
- Generates `samsung_chart.png` with the stock chart
- Displays current price, change, and percent change in the console

## Architecture

The script is a single-file data visualization pipeline:

1. **Data Collection** (lines 1-38): 
   - Disables SSL verification for Korean stock API access
   - Patches `pykrx` to use unverified sessions
   - Fetches 180-day Samsung Electronics (005930) OHLCV data

2. **Chart Generation** (lines 44-86):
   - **Top panel**: Line chart of closing prices with moving averages (MA20, MA60)
   - **Bottom panel**: Volume bar chart (color-coded: red for down days, green for up days)
   - All labels and formatting in Korean

3. **Annotations** (lines 61-72):
   - Marks highest and lowest prices in the period
   - Currency formatted with commas: `{price:,.0f}원`

4. **Output** (lines 94-102):
   - Saves PNG to disk (line 99)
   - Prints summary statistics to console with proper formatting

**Key Dependencies:**
- `pykrx`: Korean stock data API
- `matplotlib`: Charting and visualization
- `pandas`: Data manipulation

## Localization Notes

- Font: Uses `Malgun Gothic` for proper Korean character rendering (line 31)
- Minus sign: Disables unicode minus conversion to prevent display issues (line 32)
- All numeric formatting uses `f'{value:,.0f}원'` for consistency
