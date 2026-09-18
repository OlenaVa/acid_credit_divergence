"""Download FRED PZINCUSDM to data/fred_zinc.csv (run from acid_credit_divergence/)."""

import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "fred_zinc.csv")
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PZINCUSDM"


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    urllib.request.urlretrieve(URL, OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
