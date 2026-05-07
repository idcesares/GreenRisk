"""Load the TCFD recommendations corpus and print basic stats."""

from datasets import load_dataset

ds = load_dataset("climatebert/tcfd_recommendations")
print("Splits:", list(ds.keys()))
for split_name, split in ds.items():
    print(f"\n[{split_name}] {len(split)} examples")
    print("Columns:", split.column_names)
    print("First example:")
    print(split[0])

# Print the first 5 paragraphs to get a sense of the data.
print("\nFirst 5 paragraphs:")
for i in range(5):
    print(f"\n--- {i} ---")
    print(ds["train"][i]["text"])

pandas_df = ds["train"].to_pandas()
print("\nPandas DataFrame info:")
print(pandas_df.info())
print("\nPandas DataFrame head:")
print(pandas_df.head())