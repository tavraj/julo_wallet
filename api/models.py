import datetime
import enum
import os
from api import app
from flask_sqlalchemy import SQLAlchemy

import uuid

basedir = os.path.dirname(os.path.realpath(__file__))
app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'wallet.db')

# create databse instance
db = SQLAlchemy(app)
# db.create_all()
app.app_context().push()

class TransactionType(enum.Enum):
    Deposit = "deposit",
    Withdrawal = "withdrawal"

class WalletData(db.Model):
    id = db.Column(db.String(36),nullable=False, primary_key=True)
    is_enabled = db.Column(db.Boolean, default=False, nullable=False)
    balance = db.Column(db.Integer, default=0, nullable=False)

class Transactions(db.Model):
    # TransactionID(uuid), status, transacted_at, type, amount, reference_id(uuid)
    transaction_id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, nullable=False)
    reference_id = db.Column(db.String(36),nullable=False, unique=True)
    amount = db.Column(db.Integer, nullable=False)
    # withdrawal or deposit
    type = db.Column(db.Enum(TransactionType), default=TransactionType.Deposit)

