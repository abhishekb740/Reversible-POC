from fastapi import APIRouter, HTTPException
from ..types.user import UserAuth
from ..types.transaction import TransferRequest, ForceApprovalRequest
from ..db.supabase import supabase_client
from ..utils.coinbase import call_contract_function, read_contract_function, WalletType
from .auth import create_wallet

router = APIRouter(
    prefix="/transactions",
    tags=["transactions"]
)

@router.post("/transfer")       
async def transfer_money(wallet: WalletType, transfer: TransferRequest):
    try:
        # Check if recipient wallet exists, if not create one
        recipient = supabase_client.table("users").select("*").eq("wallet_address", transfer.to_wallet).execute()
        if not recipient.data:
            # Create random email for new wallet
            random_email = f"temporary@{transfer.to_wallet}.com"
            new_wallet = await create_wallet(UserAuth(email=random_email))
            transfer.to_wallet = new_wallet["response"].data[0]["wallet_address"]
            print(transfer.to_wallet)

        transfer_result = call_contract_function(wallet, "transfer", {"to": transfer.to_wallet, "amount": transfer.amount})
        if transfer_result.get('success') != True:
            raise HTTPException(status_code=500, detail="Transfer failed")
        transfer.amount = int(transfer.amount)
        transfer_index = read_contract_function(wallet, "getTransferCount", {"from": wallet.address_id, "to": transfer.to_wallet})  
        if transfer_index.get('success') != True:
            raise HTTPException(status_code=500, detail="Transfer index failed")
        transaction_data = {
            "from_wallet": wallet.address_id,
            "to_wallet": transfer.to_wallet,
            "amount": transfer.amount,
            "state": "pending",
            "index": transfer_index["result"]-1
        }
        transaction = supabase_client.table("transactions").insert(transaction_data).execute()
        
        # Get current balances
        sender = supabase_client.table("users").select("nrb_value").eq("wallet_address", wallet.address_id).execute()
        recipient = supabase_client.table("users").select("rb_value").eq("wallet_address", transfer.to_wallet).execute()
        
        # Calculate new balances
        new_sender_balance = sender.data[0]["nrb_value"] - transfer.amount
        new_recipient_balance = recipient.data[0]["rb_value"] + transfer.amount
        
        # Update sender's NRB balance
        supabase_client.table("users")\
            .update({"nrb_value": new_sender_balance})\
            .eq("wallet_address", wallet.address_id)\
            .execute()
        
        # Update recipient's RB balance
        supabase_client.table("users")\
            .update({"rb_value": new_recipient_balance})\
            .eq("wallet_address", transfer.to_wallet)\
            .execute()
        
        return {"status": "success", "transaction_id": transaction.data[0]["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/force-approval")
async def force_approval(wallet: WalletType, request: ForceApprovalRequest):
    try:
        transaction_index = supabase_client.table("transactions")\
            .select("index")\
            .eq("id", request.transaction_id)\
            .execute()
        fast_withdraw_result = call_contract_function(wallet, "fastWithdraw", {"index": transaction_index.data[0].get("index"), "from": wallet.address_id, "to": request.to_wallet})
        if fast_withdraw_result.get('success') != True:
            raise HTTPException(status_code=500, detail="Fast withdraw failed")
        
        return {"status": "success", "message": "Transaction force approved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get-transactions/{transaction_id}")
async def get_transaction(transaction_id: str):
    try:
        transaction = supabase_client.table("transactions").select("*").eq("id", transaction_id).execute()
        return {"status": "success", "data": transaction.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))