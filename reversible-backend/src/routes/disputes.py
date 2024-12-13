from fastapi import APIRouter, HTTPException
from ..types.transaction import DisputeRequest
from ..db.supabase import supabase_client
from ..utils.coinbase import call_contract_function, WalletType, read_contract_function, read_governance_function
from ..utils.useAgentAI import useAIJudge
from .judges import vote
from ..routes.auth import create_wallet
from ..types.user import UserAuth, VoteRequest
import asyncio

router = APIRouter(
    prefix="/disputes",
    tags=["disputes"]
)
@router.post("/raise-dispute")
async def raise_dispute(wallet: WalletType, request: DisputeRequest):
    try:
        transaction_index = supabase_client.table("transactions")\
            .select("index, amount")\
            .eq("id", request.transaction_id)\
            .execute()
        dispute_result = call_contract_function(wallet, "raiseDispute", {"index": transaction_index.data[0].get("index"), "from": wallet.address_id, "to": request.to_wallet})
        await asyncio.sleep(5)  # Wait for 5 seconds
        
        dispute_count = read_governance_function(wallet, "getDisputeCount", {})
        # Update transaction state to "disputed"
        transaction_update = supabase_client.table("transactions")\
            .update({"state": "disputed"})\
            .eq("id", request.transaction_id)\
            .execute()
        
        # Create new dispute entry
        dispute_data = {
            "transactionId": request.transaction_id,
            "to_wallet": request.to_wallet,
            "proof_title": request.proofTitle,
            "proof_content": request.proofContent,
            "verdict": False,
            "dispute_count": dispute_count.get("result")
        }
        dispute_result = supabase_client.table("disputes").insert(dispute_data).execute()

        ai_decision_1 = useAIJudge("base-sepolia", transaction_index.data[0].get("amount"), wallet.address_id, request.to_wallet,"", request.proofTitle, request.proofContent) 
        ai_decision_2 = useAIJudge("base-sepolia", transaction_index.data[0].get("amount"), wallet.address_id, request.to_wallet,"", request.proofTitle, request.proofContent)
        wallet_1 = await create_wallet(UserAuth(email="ai-1@judge.com"))
        wallet_2 = await create_wallet(UserAuth(email="ai-2@judge.com"))
        wallet_1 = WalletType(address_id=wallet_1["response"].data[0].get("wallet_address"), wallet_id=wallet_1["response"].data[0].get("wallet_id"), network_id=wallet_1["response"].data[0].get("network_id"))
        wallet_2 = WalletType(address_id=wallet_2["response"].data[0].get("wallet_address"), wallet_id=wallet_2["response"].data[0].get("wallet_id"), network_id=wallet_2["response"].data[0].get("network_id"))
        vote_ai_result_1 = await vote(wallet_1, VoteRequest(dispute_id=str(dispute_result.data[0].get("id")), vote=ai_decision_1))
        if vote_ai_result_1.get("status") == "success":
            vote_ai_result_2 = await vote(wallet_2, VoteRequest(dispute_id=str(dispute_result.data[0].get("id")), vote=ai_decision_2))
            if vote_ai_result_2.get("status") == "success":
                return {"status": "success", "message": "Dispute raised successfully"}
            else:
                return {"status": "error", "message": "Failed to get AI decision"}
        else:
            return {"status": "error", "message": "Failed to get AI decision"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get-disputes")
async def get_disputes():
    try:
        disputes = supabase_client.table("disputes").select("*").execute()
        return {"status": "success", "data": disputes.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get-dispute/{dispute_id}")
async def get_dispute(dispute_id: str):
    try:
        dispute = supabase_client.table("disputes").select("*").eq("id", dispute_id).execute()
        return {"status": "success", "data": dispute.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/getVotes/{dispute_id}")
async def get_votes(dispute_id: str):
    try:
        # Get all votes for this dispute
        votes = supabase_client.table("judges")\
            .select("vote")\
            .eq("dispute_id", dispute_id)\
            .execute()
        
        # Count pass and fail votes
        pass_votes = len([v for v in votes.data if v["vote"] == "1"])
        fail_votes = len([v for v in votes.data if v["vote"] == "2"])
        
        return {
            "status": "success", 
            "data": {
                "pass_votes": pass_votes,
                "fail_votes": fail_votes
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

