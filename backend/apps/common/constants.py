"""Project-wide constants — single source of truth, avoid magic strings."""


class UserRole:
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

    CHOICES = [
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (MEMBER, "Member"),
        (VIEWER, "Viewer"),
    ]


class TransactionType:
    INCOME = "income"
    EXPENSE = "expense"
    LOAN_GIVEN = "loan_given"
    LOAN_TAKEN = "loan_taken"
    TRANSFER = "transfer"

    CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
        (LOAN_GIVEN, "Loan Given"),
        (LOAN_TAKEN, "Loan Taken"),
        (TRANSFER, "Transfer"),
    ]


DEFAULT_CURRENCY = "INR"
