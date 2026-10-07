"""
dataset_generator.py
--------------------
Creates the "Synthetic/Simulated Sample Dataset for Academic Use".

IMPORTANT: none of these numbers are real laboratory measurements.

How the data is simulated (physics-inspired, but simplified):
  1. A "true" gold purity is drawn for each sample. About 60% are close to
     common jewellery grades (9K, 14K, 18K, 22K, 24K); the rest are spread evenly.
  2. The remaining (100 - purity)% is the alloy. It is split between copper,
     silver, zinc and nickel using a random "alloy style" (yellow, rose, white)
     plus a small share of unmeasured trace metals.
  3. Density follows the rule of mixtures 1/rho = sum(w_i / rho_i), with small
     casting-porosity, temperature and measurement noise.
  4. The XRF-like reading is the true purity plus noise, a small matrix effect,
     a temperature drift, and (for ~8% of samples) a surface-plating bias that
     makes the reading over-estimate the purity.
  5. Each measured value gets its own noise, so the target purity is NOT equal
     to any single input column and the models have real patterns to learn.
"""

import numpy as np
import pandas as pd

from src import config

# Pure-metal densities in g/cm3 (approximate textbook values).
RHO = {"gold": 19.32, "copper": 8.96, "silver": 10.49, "zinc": 7.14,
       "nickel": 8.91, "other": 9.0}

# Typical grades of jewellery gold (purity in %).
STANDARD_GRADES = np.array([37.5, 58.5, 75.0, 91.6, 99.9])

# Share of the alloy taken by [copper, silver, zinc, nickel] for each style.
ALLOY_STYLES = {
    "yellow": [0.45, 0.45, 0.10, 0.02],
    "rose":   [0.85, 0.08, 0.06, 0.02],
    "white":  [0.15, 0.30, 0.15, 0.40],
}


def _draw_purity(rng, n):
    """Draw true gold purity values (in %)."""
    grade = rng.choice(STANDARD_GRADES, size=n)
    near_grade = np.where(
        grade > 99.0,
        99.95 - np.abs(rng.normal(0, 0.7, n)),   # stay just below 100
        rng.normal(grade, 1.5),
    )
    spread = rng.uniform(40.0, 99.9, n)
    use_grade = rng.random(n) < 0.6
    return np.clip(np.where(use_grade, near_grade, spread), 35.0, 99.95)


def _split_alloy(rng, alloy_total):
    """Split the alloy share into copper, silver, zinc, nickel (+ trace metals)."""
    n = len(alloy_total)
    trace = alloy_total * rng.uniform(0.0, 0.03, n)          # unmeasured metals
    measurable = alloy_total - trace
    style_names = list(ALLOY_STYLES)
    style_idx = rng.integers(0, len(style_names), n)
    shares = np.zeros((n, 4))
    for i, name in enumerate(style_names):
        rows = np.where(style_idx == i)[0]
        alpha = np.maximum(np.array(ALLOY_STYLES[name]) * 25.0, 0.3)
        shares[rows] = rng.dirichlet(alpha, size=len(rows))
    parts = shares * measurable[:, None]
    return parts, trace


def generate_dataset(n_records=1200, seed=config.RANDOM_STATE):
    """Return a DataFrame with `n_records` synthetic gold samples."""
    rng = np.random.default_rng(seed)
    n = int(n_records * 1.05) + 10          # a few extra, in case duplicates are dropped

    purity = _draw_purity(rng, n)
    parts, trace = _split_alloy(rng, 100.0 - purity)
    cu, ag, zn, ni = parts.T

    temperature = np.clip(rng.normal(25, 4, n), 10, 40)
    weight = np.clip(np.exp(rng.normal(np.log(8), 0.7, n)), 0.5, 200)

    # --- density: rule of mixtures + porosity + temperature + noise -------
    inverse_density = (purity / RHO["gold"] + cu / RHO["copper"] + ag / RHO["silver"]
                       + zn / RHO["zinc"] + ni / RHO["nickel"] + trace / RHO["other"]) / 100.0
    density = 1.0 / inverse_density
    density *= 1.0 - rng.uniform(0.0, 0.012, n)               # casting porosity
    density *= 1.0 - 4.2e-5 * (temperature - 20.0)            # thermal expansion
    density += rng.normal(0, 0.05 + 0.6 / (1.0 + weight))     # small samples -> noisier

    # --- measured alloy percentages (each has its own noise) ---------------
    def measure(true_value, cap):
        noisy = true_value * (1 + rng.normal(0, 0.04, n)) + rng.normal(0, 0.10, n)
        return np.clip(noisy, 0, cap)

    copper = measure(cu, 60)
    silver = measure(ag, 60)
    zinc = measure(zn, 30)
    nickel = measure(ni, 30)

    # --- XRF-like gold reading --------------------------------------------
    xrf = (purity
           + rng.normal(0, 2.5, n)                            # counting noise
           + rng.normal(0, 1.0, n) * 0.05 * (100 - purity)    # matrix effect
           + 0.02 * (temperature - 25.0))                     # slight drift
    plated = rng.random(n) < 0.08                             # gold-plated surface
    xrf = xrf + plated * rng.uniform(3.0, 10.0, n)
    xrf = np.clip(xrf, 0, 100)

    df = pd.DataFrame({
        "density": np.round(np.clip(density, 5.0, 19.9), 3),
        "copper_percent": np.round(copper, 3),
        "silver_percent": np.round(silver, 3),
        "zinc_percent": np.round(zinc, 3),
        "nickel_percent": np.round(nickel, 3),
        "xrf_gold_reading": np.round(xrf, 2),
        "temperature": np.round(temperature, 1),
        "weight": np.round(weight, 2),
        "purity": np.round(purity, 2),
    })
    df = df.drop_duplicates().head(n_records).reset_index(drop=True)
    return df


def print_summary(df):
    """Print the short summary requested for the generated dataset."""
    print("=" * 60)
    print(config.DATASET_LABEL)
    print("=" * 60)
    print(f"Number of records : {len(df)}")
    print(f"Number of features: {len(config.FEATURE_COLUMNS)}")
    print(f"Minimum purity    : {df[config.TARGET_COLUMN].min():.2f} %")
    print(f"Maximum purity    : {df[config.TARGET_COLUMN].max():.2f} %")
    print(f"Mean purity       : {df[config.TARGET_COLUMN].mean():.2f} %")
    print("NOTE: values are simulated, not real laboratory measurements.")


def generate_and_save(path=None, n_records=1200, seed=config.RANDOM_STATE):
    """Generate the dataset, save it as CSV and print the summary."""
    path = path or config.DATASET_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset(n_records, seed)
    df.to_csv(path, index=False)
    print_summary(df)
    print(f"Saved to: {path}")
    return df


if __name__ == "__main__":
    generate_and_save()
