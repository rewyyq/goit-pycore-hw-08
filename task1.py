import re
from collections import UserDict
from functools import wraps
from datetime import datetime, date, timedelta
import pickle

DATE_FORMAT = "%d.%m.%Y"

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Birthday(Field):
    def __init__(self, value):
        try:
            parsed = datetime.strptime(value, DATE_FORMAT)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        if parsed.date() > date.today():
            raise ValueError("Birthday cannot be in the future.")
        super().__init__(parsed)
    def __str__(self):
        return self.value.strftime(DATE_FORMAT)

class Name(Field):
    def __init__(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty")
        super().__init__(value.strip().capitalize())

class Phone(Field):
    def __init__(self, value):
        if not re.fullmatch(r"[0-9]{10}", value):
            raise ValueError("Invalid phone number format")
        super().__init__(value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        phone_num_to_remove = self.find_phone(phone_number)
        if phone_num_to_remove:
            self.phones.remove(phone_num_to_remove)

    def edit_phone(self, old_phone, new_phone):
        is_number_exists = self.find_phone(old_phone)
        if is_number_exists:
            validated_new_phone = Phone(new_phone)
            is_number_exists.value = validated_new_phone.value
        else:
            raise ValueError(f"Phone {old_phone} not found")
        
    def add_birthday(self, date):
        self.birthday = Birthday(date)
        
    def find_phone(self, phone_number):
        for phones in self.phones:
            if phones.value == phone_number:
                return phones
        return None

    def __str__(self):
        bday = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{bday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record
    def find(self, name):
        return self.data.get(name.strip().capitalize())
    def delete(self, name):
        normalized_name = name.strip().capitalize()
        if normalized_name in self.data:
            del self.data[normalized_name]
    def get_upcoming_birthdays(self):
        res = []
        today = datetime.today().date()
        for record in self.data.values():
            if record.birthday is None:
                continue
            user_birthday = record.birthday.value.date()
            user_birthday = user_birthday.replace(year=today.year)
            username = record.name.value
            days_difference = (user_birthday - today).days
            if days_difference <= -3:               
                user_birthday = user_birthday.replace(year=today.year + 1)
                days_difference = (user_birthday - today).days
            if -2 <= days_difference <= 7:           
                current_week_day = user_birthday.weekday()
                if current_week_day == 5:
                    new_date = user_birthday + timedelta(days=2)    
                elif current_week_day == 6:
                    new_date = user_birthday + timedelta(days=1)
                else:
                    new_date = user_birthday
                if new_date >= today:
                    res.append({"name": username, "congratulation_date": new_date.strftime("%d.%m.%Y")})
        return res


def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command."
    return inner

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Contact changed."

@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    return "; ".join(phone.value for phone in record.phones)

@input_error
def show_all(book: AddressBook):
    if not book.data:
        return "Address book is empty"
    return "\n".join(str(record) for record in book.data.values())

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return "Birthday added"

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday:
        return str(record.birthday)
    return "Birthday not set"

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next week"
    return "\n".join(f"{item['congratulation_date']}: {item['name']}" for item in upcoming)


def save_data(book, filename = "addressbook.pkl"):
    with open(filename, 'wb') as f:
        pickle.dump(book, f)

def load_data(filename = "addressbook.pkl"):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    try:
        while True:
            user_input = input("Enter a command: ")
            if not user_input.strip():
                continue
            command, *args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                save_data(book)
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(args, book))
            else:
                print("Invalid command.")
    finally:
        save_data(book)

if __name__ == "__main__":
    main()