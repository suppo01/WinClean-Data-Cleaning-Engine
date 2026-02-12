import os


def main():
    # Raise runtime path errors
    print(os.listdir("C:\\nonexistent\\path"))
    print(os.listdir("C:\\Users\\molly\\COM1"))
    print(os.listdir("C:\\Users\\molly\\github>"))


if __name__ == "__main__":
    main()
