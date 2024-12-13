from fastapi import APIRouter, HTTPException
from ..types.user import UserAuth
from ..db.supabase import supabase_client
from ..utils.coinbase import create_coinbase_wallet_address

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/create-wallet")
async def create_wallet(user: UserAuth):
    try:

        wallet = supabase_client.table("users").select("*").eq("email", user.email).execute()

        if not wallet.data:
            wallet_address = create_coinbase_wallet_address()
            print(wallet_address)
            address_id = wallet_address.get("address")
            wallet_id = wallet_address.get("wallet_id")
            network_id = wallet_address.get("network_id")
            wallet = supabase_client.table("users").insert({
                "wallet_address": address_id,
                "wallet_id": wallet_id,
                "email": user.email,
                "network_id": network_id
            }).execute()
            
        return {"status": "success", "response": wallet}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))