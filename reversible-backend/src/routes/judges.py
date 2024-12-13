from fastapi import APIRouter, HTTPException
from ..db.supabase import supabase_client
from ..types.user import VoteRequest
from ..utils.coinbase import call_contract_function, WalletType, call_governance_function
from ..types.transaction import ReverseTransactionRequest
router = APIRouter(
    prefix="/judges",
    tags=["judges"]
)

def reverse_transaction(request: ReverseTransactionRequest):
    try:
        transaction_update = supabase_client.table("transactions")\
            .update({"state": "reversed"})\
            .eq("id", request.transaction_id)\
            .execute()
        
        # Get transaction details
        transaction = supabase_client.table("transactions")\
            .select("*")\
            .eq("id", request.transaction_id)\
            .execute()
        
        if transaction.data:
            amount = transaction.data[0]["amount"]
            from_wallet = transaction.data[0]["from_wallet"]
            to_wallet = transaction.data[0]["to_wallet"]
            
            # Get current balances
            recipient = supabase_client.table("users").select("rb_value").eq("wallet_address", to_wallet).execute()
            sender = supabase_client.table("users").select("nrb_value").eq("wallet_address", from_wallet).execute()
            
            # Calculate new balances
            new_recipient_rb = recipient.data[0]["rb_value"] - amount
            new_sender_nrb = sender.data[0]["nrb_value"] + amount
            
            # Return amount from recipient's RB to sender's NRB
            supabase_client.table("users")\
                .update({"rb_value": new_recipient_rb})\
                .eq("wallet_address", to_wallet)\
                .execute()
            
            supabase_client.table("users")\
                .update({"nrb_value": new_sender_nrb})\
                .eq("wallet_address", from_wallet)\
                .execute()
        
        return {"status": "success", "message": "Transaction reversed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def reject_reverse_transaction(request: ReverseTransactionRequest):
    try:
        # Update transaction state to "completed"
        transaction_update = supabase_client.table("transactions")\
            .update({"state": "completed"})\
            .eq("id", request.transaction_id)\
            .execute()
        
        # Get transaction details
        transaction = supabase_client.table("transactions")\
            .select("*")\
            .eq("id", request.transaction_id)\
            .execute()
        
        if transaction.data:
            recipient = transaction.data[0]["to_wallet"]
            sender = transaction.data[0]["from_wallet"]
            amount = transaction.data[0]["amount"]
            
            # Get current balances
            recipient_balance = supabase_client.table("users").select("rb_value, nrb_value").eq("wallet_address", recipient).execute()

            current_rb = recipient_balance.data[0]["rb_value"]
            current_nrb = recipient_balance.data[0]["nrb_value"]
            
            # Move amount from RB to NRB balance for recipient
            supabase_client.table("users")\
                .update({
                    "rb_value": current_rb - amount,
                })\
                .eq("wallet_address", recipient)\
                .execute()
            supabase_client.table("users")\
                .update({
                    "nrb_value": current_nrb + amount
                })\
                .eq("wallet_address", recipient)\
                .execute()
        
        return {"status": "success", "message": "Transaction reversal rejected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/vote")
async def vote(wallet: WalletType, request: VoteRequest):
    try:
        dispute_count = supabase_client.table("disputes").select("dispute_count").eq("id", request.dispute_id).execute()
        # Convert string vote to enum value
        vote_result = call_governance_function(wallet, "voteAndResolve", {
            "_disputeId": dispute_count.data[0].get("dispute_count"), 
            "_vote": request.vote
        })
        # if vote_result.get('success') != True:
        #     raise HTTPException(status_code=500, detail="Vote failed")
        # Add vote to judges table
        judge_vote = supabase_client.table("judges").insert({
            "wallet_address": wallet.address_id,
            "dispute_id": request.dispute_id,
            "vote": request.vote
        }).execute()

        # Get total votes for this dispute
        votes = supabase_client.table("judges")\
            .select("vote")\
            .eq("dispute_id", request.dispute_id)\
            .execute()
        
        # Count pass votes
        pass_votes = len([v for v in votes.data if v["vote"] == "1"])
        fail_votes = len([v for v in votes.data if v["vote"] == "2"])
        total_votes = 5
        
        # Check if passes threshold
        if pass_votes >= (total_votes // 2) + 1:
            # Get dispute details
            dispute = supabase_client.table("disputes")\
                .select("transactionId")\
                .eq("id", request.dispute_id)\
                .execute()
            
            if dispute.data:
                transaction_id = dispute.data[0]["transactionId"]
                
                # Update dispute verdict
                dispute_update = supabase_client.table("disputes")\
                    .update({"verdict": True})\
                    .eq("id", request.dispute_id)\
                    .execute()
                
                # Get transaction details for to_wallet
                transaction = supabase_client.table("transactions")\
                    .select("to_wallet")\
                    .eq("id", transaction_id)\
                    .execute()
                
                if transaction.data:
                    transaction_id = str(transaction_id)
                    # Call reverse transaction
                    reverse_transaction(ReverseTransactionRequest(
                        transaction_id=transaction_id,
                        to_wallet=transaction.data[0].get("to_wallet")
                    ))

        elif fail_votes >= (total_votes // 2) + 1:
            # Get dispute details
            dispute = supabase_client.table("disputes")\
                .select("transactionId")\
                .eq("id", request.dispute_id)\
                .execute()
            
            if dispute.data:
                transaction_id = dispute.data[0]["transactionId"]
            
                transaction = supabase_client.table("transactions")\
                    .select("to_wallet")\
                    .eq("id", transaction_id)\
                    .execute()
                
                if transaction.data:
                    transaction_id = str(transaction_id)
                    # Call reverse transaction
                    reject_reverse_transaction(ReverseTransactionRequest(
                        transaction_id=transaction_id,
                        to_wallet=transaction.data[0].get("to_wallet")
                    ))

        return {"status": "success", "message": "Vote submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    