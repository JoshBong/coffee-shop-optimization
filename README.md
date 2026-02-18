# NYC Coffee Shop Location Optimizer

A profit-maximization model for identifying optimal coffee shop locations across New York City, balancing pedestrian foot traffic against commercial rent costs.

## Overview

The conventional wisdom for opening a retail business is to find the highest-traffic location you can afford. This project challenges that assumption. Using NYC pedestrian count data and real commercial rent listings, I built a linear optimization model in Python that determines which of 114 candidate locations across the five boroughs would yield the highest daily profit for a coffee shop — and the results are counterintuitive.

**Key finding:** The highest-traffic location in the dataset (29,247 average daily pedestrians) was outperformed by a location with 33% less foot traffic, purely because of rent efficiency. Only 48 of 114 locations (≈40%) cleared a sustainable $500/day profit threshold.

---

## Model Formulation

The model maximizes daily profit across all candidate locations and time periods using Gurobi.

### Objective Function

$$\text{Maximize } \sum_{i \in L} \left[ \sum_{t \in T} f_i^t \cdot c^t \cdot p \cdot x_i - r_i \cdot s \right] - (w \cdot n)$$

### Sets

| Symbol | Description |
|--------|-------------|
| $T = \{\text{AM, MD, PM}\}$ | Time periods (morning, midday, evening) |
| $L$ | Set of candidate locations |

### Parameters

| Symbol | Description |
|--------|-------------|
| $f_i^t$ | Foot traffic at location $i$ during time period $t$ |
| $c^t$ | Conversion rate (pedestrians → paying customers) |
| $p$ | Average profit per customer |
| $r_i$ | Rent per square foot at location $i$ |
| $s$ | Shop size in square feet |
| $w$ | Average hourly wage per staff member |
| $n$ | Number of staff members |

### Decision Variables

| Variable | Type | Description |
|----------|------|-------------|
| $y_i$ | $\{0, 1\}$ | Whether to open a shop at location $i$ |
| $x_t$ | $\{0, 1\}$ | Whether to operate during time period $t$ |

### Constraints

- $n = 2$ — Minimum 2 staff members at all times  
- $x_\text{AM} + x_\text{MD} + x_\text{PM} \geq 2$ — Shop must operate during at least 2 time periods  
- $\text{Profit} \geq 500 \cdot y_i$ — Only open a location if it clears $500/day

---

## Data Sources

**Pedestrian Traffic — [NYC Bi-Annual Pedestrian Counts](https://data.cityofnewyork.us/Transportation/Bi-Annual-Pedestrian-Counts/2de2-6x2h)**  
Collected by the NYC Department of Transportation every May and September at 114 locations across the city, primarily in neighborhood retail corridors. Counts are recorded mid-block during three windows: weekday morning (7–9 AM), weekday evening (4–7 PM), and Saturday midday (12–2 PM) — which map directly to the AM/MD/PM time periods in the model.

**Commercial Rent — [LoopNet](https://www.loopnet.com)**  
Rather than using a single city-wide average, I manually defined geographic bounding boxes (by latitude/longitude) for distinct NYC neighborhoods and pulled average retail rent per square foot from active listings in each zone. Manhattan rents in the dataset range from $50 to $200/sqft annually, with significant variation by neighborhood.

Example rent zones from the assignment dictionary:
```python
{
    "Midtown East":  {"lat_min": 40.7520, "lat_max": 40.7720, "lon_min": -73.9840, "lon_max": -73.9620, "rent": 125.86},
    "Midtown West":  {"lat_min": 40.7530, "lat_max": 40.7680, "lon_min": -74.0070, "lon_max": -73.9840, "rent": 122.94},
    "Bronx":         {"lat_min": 40.7710, "lat_max": 40.9160, "lon_min": -73.9660, "lon_max": -73.8250, "rent": 64.31},
}
```

---

## Assumptions

| Parameter | Value | Source |
|-----------|-------|--------|
| Shop sizes modeled | 600, 800, 1,000 sq ft | Industry average |
| Pedestrian entry rate | 10% | Pedestrian consumer behavior research |
| Purchase conversion rate | 8% of total pedestrians | Estimated from entry rate |
| Average profit per customer | $5.00 | NYC avg. coffee price ($6–7) minus COGS |
| Staff wages | $20/hr per worker | Above NYC minimum wage ($16.50) |
| Minimum staff | 2 at all times | Model constraint |
| Utilities | Included in rent for <1,000 sq ft | Standard NYC lease terms |

---

## Results

Running the model at 1,000 sq ft with an 8% customer conversion rate:

- **Top location (Location 3):** $8,414/day profit — 2,282 daily customers, $64.31/sqft rent
- **Busiest location (Location 42):** Lower profit despite 29,247 daily pedestrians — rent of $125.86/sqft eroded margins
- **48 of 114 locations** (42%) met the $500/day profitability threshold
- All top-performing locations operated across all three time periods (AM, MD, PM), confirming that maximizing operating hours spreads fixed rent costs and improves returns

The geographic pattern is clear: optimal locations cluster around areas with moderate foot traffic and below-market rent, not the city's most visible corridors.

| Location | Rent ($/sqft/mo) | Daily Profit | Daily Customers | Daily Revenue |
|----------|-----------------|--------------|-----------------|---------------|
| 3        | 64.31           | $8,414.93    | 2,282           | $11,413.60    |
| 49       | 125.86          | $7,678.87    | 2,545           | $12,729.20    |
| 92       | 44.03           | $6,936.93    | 1,851           | $9,259.60     |
| 42       | 125.86          | $6,644.47    | 2,338           | $11,694.80    |
| 23       | 62.97           | $5,501.20    | 1,691           | $8,455.20     |

---

## Tech Stack

- **Python** — core analysis and modeling
- **Pandas** — data preprocessing and manipulation
- **Gurobi** — linear optimization solver
- **Folium** — interactive map visualizations

---

## File Structure

```
coffee-shop-optimization/
├── README.md
├── .gitignore
├── data/
│   └── Bi-Annual_Pedestrian_Counts_20250423.csv
├── src/
│   ├── optimizer.py          # Main optimization model
│   ├── map.py                # Folium map generation
│   └── get_neighborhood.py   # Rent zone assignment by lat/lon
└── output/
    └── coffee_shop_locations.html  # Interactive map of results
```
