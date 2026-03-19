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
    print("Generator numerów celu")

    while True:
        print("\n1 - kod liczbowy (np. 4563 8975)")
        print("2 - kod alfanumeryczny (8 losowych znaków, np. R57A839K)")
        print("3 - zakończ")
        choice = input("Wybierz typ generatora (1, 2 lub 3): ").strip()

        if choice == "1":
            print("Wygenerowany kod:", generate_numeric_code())

        elif choice == "2":
            print("Wygenerowany kod:", generate_alphanumeric_code())

        elif choice == "3":
            print("Koniec programu.")
            break

        else:
            print("Nieprawidłowy wybór. Spróbuj ponownie.")


if __name__ == "__main__":
    main()
