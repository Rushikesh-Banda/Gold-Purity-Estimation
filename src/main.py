"""
main.py
-------
Command-line entry point.

    python -m src.main generate   # create data/gold_dataset.csv
    python -m src.main train      # train + evaluate + save best model + graphs
    python -m src.main gui        # start the Tkinter application
    python -m src.main all        # generate + train
"""

import argparse
import sys

from src import config


def main(argv=None):
    parser = argparse.ArgumentParser(description=config.APP_TITLE)
    parser.add_argument("command", choices=["generate", "train", "gui", "all"])
    args = parser.parse_args(argv)
    config.ensure_directories()

    if args.command in ("generate", "all"):
        from src.dataset_generator import generate_and_save
        generate_and_save()
    if args.command in ("train", "all"):
        from src.train_model import main as train_main
        train_main()
    if args.command == "gui":
        try:
            from gui.app import run_app
        except ImportError as error:
            print(f"Could not start the GUI: {error}\n"
                  "Tkinter is part of Python; on Linux install it with: sudo apt install python3-tk")
            sys.exit(1)
        run_app()


if __name__ == "__main__":
    main()
