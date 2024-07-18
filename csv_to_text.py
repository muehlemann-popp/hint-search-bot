from argparse import ArgumentParser
from pathlib import Path
from typing import Iterator
from itertools import islice


def csv_to_text(input: Path) -> Iterator[str]:
    import pandas as pd

    df = pd.read_csv(input, delimiter=";")
    for row, data in df.iterrows():
        buf = ""
        for column, value in data.items():
            if column != "Unnamed: 0":
                buf = buf + f"{column}: {value}\n"
        yield buf


if __name__ == "__main__":
    parser = ArgumentParser(
        prog="csv_to_text",
        description="Convert a CSV file to text.",
    )
    parser.add_argument("input", type=Path, help="Input CSV file")
    parser.add_argument("output", type=Path, help="Output TXT file")
    args = parser.parse_args()

    with open(args.output, 'w') as f:
        for str in csv_to_text(args.input):
            f.write(str + '\n')
