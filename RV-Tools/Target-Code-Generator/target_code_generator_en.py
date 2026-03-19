import random
import string


def generate_numeric_code(groups=(4, 4)) -> str:
    """Generate a numeric target code, e.g. 4563 8975."""
    return " ".join(
        "".join(random.choice(string.digits) for _ in range(length))
        for length in groups
    )


def generate_alphanumeric_code(total_length=8) -> str:
    """Generate an alphanumeric target code with random letters/digits, e.g. R57A839K."""
    chars = []
    for _ in range(total_length):
        chars.append(random.choice(string.ascii_uppercase + string.digits))
    return "".join(chars)


def main() -> None:
    print("Target Code Generator")

    while True:
        print("\n1 - numeric code (e.g. 4563 8975)")
        print("2 - alphanumeric code (8 random characters, e.g. R57A839K)")
        print("3 - exit")
        choice = input("Choose generator type (1, 2, or 3): ").strip()

        if choice == "1":
            print("Generated code:", generate_numeric_code())

        elif choice == "2":
            print("Generated code:", generate_alphanumeric_code())

        elif choice == "3":
            print("Program finished.")
            break

        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
