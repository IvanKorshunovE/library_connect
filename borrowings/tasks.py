from datetime import date, timedelta

from celery import shared_task

from borrowings.models import Borrowing
from borrowings.telegram_notification import send_to_telegram


@shared_task
def send_overdue_borrowings():
    current_date = date.today()
    formatted_date = current_date.strftime("%B %d, %Y")
    tomorrow = date.today() + timedelta(days=1)
    overdue_borrowings = Borrowing.is_active.filter(
        expected_return_date__lte=tomorrow,
    ).prefetch_related("user", "book")

    if overdue_borrowings:
        messages = [
            f"Overdue borrowings, date: {formatted_date}"
        ]
        for borrowing in overdue_borrowings:
            book = borrowing.book
            user = borrowing.user
            first_name = (
                f"{user.first_name}" if user.first_name
                else "not specified"
            )
            last_name = (
                f"{user.last_name}" if user.last_name
                else "not specified"
            )
            time_difference = (
                    borrowing.expected_return_date
                    - borrowing.borrow_date
            )
            expected_price = book.daily_fee * time_difference.days
            # expected_price = book.daily_fee

            message = (
                f"Borrowing ID: {borrowing.id},\n\n"
                f"Borrower information:\n"
                f"borrower id: {borrowing.user_id}\n"
                f"borrower email: {user.email},\n"
                f"borrower first name: {first_name}\n"
                f"borrower last name: {last_name}\n\n"
                f"Book:\n"
                f"Title: {book.title},\n"
                f"Author: {book.author},\n"
                f"Cover: {book.get_cover_display()}\n\n"
                f"The total price is: {expected_price}$"
            )
            messages.append(message)

        for message in messages:
            send_to_telegram(message)
    else:
        send_to_telegram(
            f"date: {formatted_date}. No overdue books today"
        )
