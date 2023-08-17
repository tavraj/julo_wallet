import datetime
from flask import request,jsonify, make_response
from api import app
from functools import wraps
from .models import TransactionType, db, WalletData, Transactions

import jwt

with app.app_context():
    db.create_all()

# This is called before every API expect init. Checks for Auth token and returns customer data if successful
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization']

        if not token:
            return jsonify({'message' : 'Auth Token is missing!'}), 401

        try: 
            data = jwt.decode(token, key="My Super Strong Key !@#$%$#@!", options={"verify_signature": False})
            xid = data['customer_id']
            # search if xid exists in table or not
            # cust_data = WalletData.query.get(xid)
            customer_data = db.get_or_404(WalletData, ident=xid)
            if not customer_data:
                return jsonify({'message' : 'No customer data found for given token'}), 401
        except Exception as e:
            return jsonify({'message' : 'Token is invalid!'}), 401

        return f(customer_data, *args, **kwargs)

    return decorated


@app.route("/api/v1/init", methods=['POST'])
def Initialize():
    # get customer id
    xid = request.form.get('customer_xid')
    if not xid :
        return make_response('Could not verify', 400, {'WWW-Authenticate' : 'Basic realm="Customer Id required!"'})
    
    # otherwise create a new jwt based on xid
    payload = {'customer_id': xid}
    token = jwt.encode(payload, key="My Super Strong Key !@#$%$#@!", algorithm="HS256")

    header = jwt.decode(token, options={"verify_signature": False})
    print(header)

    db.session.add(WalletData(id=xid))
    db.session.commit()
    return jsonify({ "status": "success", "data": {'token' : token} })

@app.route("/api/v1/wallet", methods=["POST"])
@token_required
def EnableWallet(wallet_data):
    if wallet_data.is_enabled is True:
        return make_response(jsonify({ "status": "fail","data": {"error": "Already enabled"}}), 400)
    wallet_data.is_enabled = True
    db.session.commit()
    current_time = 123456789
    response = {
        "status": "success",
        "data": {
            "wallet": {
                "id": wallet_data.id,
                "owned_by": wallet_data.id,
                "status": "enabled",
                "enabled_at": current_time,
                "balance": wallet_data.balance,
            }
        }
    }
    return jsonify(response)


@app.route("/api/v1/balance", methods=['GET'])
@token_required
def ViewBalance(wallet_data):
    if wallet_data.is_enabled is False:
        return make_response(jsonify({ "status": "fail","data": {"error": "Wallet Disabled"}}), 400)
    response = {
        "status": "success",
        "data": {
            "wallet": {
                "id": wallet_data.id,
                "owned_by": wallet_data.id,
                "status": "enabled",
                "balance": wallet_data.balance,
            }
        }
    }
    return make_response(jsonify(response), 200)
    


@app.route("/api/v1/wallet/transactions", methods=['GET'])
@token_required
def ViewTransactions(wallet_data):
    transactions = Transactions.query.filter(Transactions.wallet_id == wallet_data.id).all()

    transactions_list = []
    for transaction in transactions:
        transaction_data = {
            "transaction_id": str(transaction.transaction_id),
            "amount": transaction.amount,
            "type": transaction.type.value
        }
        transactions_list.append(transaction_data)

    response = {
        "status": "success",
        "data": {
            "transactions": transactions_list
        }
    }

    return make_response(jsonify(response), 200)


@app.route("/api/v1/wallet/deposits", methods=['POST'])
@token_required
def deposit(wallet_data):
    ref_id = request.form.get('reference_id')
    amount = request.form.get('amount')
    transaction = Transactions(wallet_id = wallet_data.id, amount=amount, reference_id = ref_id, type = TransactionType.Deposit)
    db.session.add(transaction)
    wallet_data.balance = wallet_data.balance + int(amount)
    db.session.commit()
    

    response = {
        "status": "success",
        "data": {
            "deposit": {
                "id": transaction.transaction_id,
                "deposited_by": transaction.wallet_id,
                "status": "success",
                "amount": transaction.amount,
                "reference_id": ref_id
            }
        }
    }

    return make_response(jsonify(response), 200)



@app.route("/api/v1/wallet/withdrawals", methods=['POST'])
@token_required
def withdraw(wallet_data):
    ref_id = request.form.get('reference_id')
    amount = request.form.get('amount')
    transaction = Transactions(wallet_id = wallet_data.id, amount=amount, reference_id = ref_id, type = TransactionType.Withdrawal)
    db.session.add(transaction)
    wallet_data.balance = wallet_data.balance - int(amount)
    if wallet_data.balance<0:
        return jsonify({'message' : 'insufficient balance'}), 401
    db.session.commit()
    

    response = {
        "status": "success",
        "data": {
            "deposit": {
                "id": transaction.transaction_id,
                "deposited_by": transaction.wallet_id,
                "status": "success",
                "amount": transaction.amount,
                "reference_id": ref_id
            }
        }
    }

    return make_response(jsonify(response), 200)

@app.route("/api/v1/wallet", methods=['PATCH'])
@token_required
def DisableWallet(wallet_data):
    wallet_data.is_enabled = False  # Disable the wallet by setting is_enabled to False
    db.session.commit()

    response = {
        "status": "success",
        "data": {
            "message": "Wallet has been disabled."
        }
    }
    return make_response(jsonify(response), 200)
