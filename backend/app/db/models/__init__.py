# Import all models so Alembic can discover them for autogenerate
from app.db.models.user import User
from app.db.models.property import Property
from app.db.models.unit import Unit
from app.db.models.loan import Loan
from app.db.models.expense import Expense
from app.db.models.scenario import Scenario

__all__ = ["User", "Property", "Unit", "Loan", "Expense", "Scenario"]
