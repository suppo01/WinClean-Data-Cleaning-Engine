import os


def main():
    # Raise runtime path errors with error handling
    paths_to_test = [
        r"C:\\nonexistent\\path",
        r"C:\\Users\\molly\\COM1",
        r"C:\\Users\\molly\\github>",
    ]

    for path in paths_to_test:
        try:
            print(f"Contents of {path}: {os.listdir(path)}")
        except OSError as error:
            print(f"Error accessing {path}: {error}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
