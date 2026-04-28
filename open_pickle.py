import pickle
import sys

# ================================================
# open_pickle.py — inspect any .pkl file safely
# Usage: python open_pickle.py
# Change FILE_TO_CHECK to whichever file you want
# ================================================

FILE_TO_CHECK = "tfidf_matrix.pkl"   # change to: df.pkl / indices.pkl / tfidf.pkl

# numpy compatibility fix (needed for pickles built on older numpy)
import numpy
sys.modules.setdefault("numpy._core",         numpy.core)
sys.modules.setdefault("numpy._core.numeric", numpy.core.numeric)

print(f"\n📂 Opening: {FILE_TO_CHECK}")

try:
    with open(FILE_TO_CHECK, "rb") as f:
        data = pickle.load(f, encoding="latin1")

    print(f"✅ Loaded successfully!")
    print(f"   Type    : {type(data)}")

    # Extra info depending on type
    if hasattr(data, "shape"):
        print(f"   Shape   : {data.shape}")

    if hasattr(data, "columns"):
        print(f"   Columns : {list(data.columns)}")
        print(f"   Rows    : {len(data)}")
        print(f"   Sample  :\n{data.head(3)}")

    elif hasattr(data, "items"):
        items = list(data.items())[:5]
        print(f"   Length  : {len(data)}")
        print(f"   Sample  : {items}")

    elif hasattr(data, "__len__"):
        print(f"   Length  : {len(data)}")

except FileNotFoundError:
    print(f"❌ File not found: {FILE_TO_CHECK}")
    print("   Make sure you run this from the project folder.")
except Exception as e:
    print(f"❌ Failed to load: {e}")