from cdp import *
from src.config.env import Env
from pydantic import BaseModel
from src.utils.contract import ERC20R_ADDRESS, ERC20R_ABI, GOVERNANCE_ADDRESS, GOVERNANCE_ABI
from cdp.smart_contract import SmartContract
import os  # Add this import at the top


api_key_name = Env.COINBASE_API_KEY_NAME
api_key_private_key = Env.COINBASE_API_KEY_SECRET

class EmailStr(BaseModel):
    email: str

class WalletType(BaseModel):
    address_id: str
    wallet_id: str
    network_id: str

def create_coinbase_wallet_address():
    try:
        Cdp.configure_from_json("src/utils/cdp_api_key.json")
        wallet = Wallet.create()
        address = wallet.default_address
        faucet_tx = wallet.faucet()
        faucet_tx.wait()
        
        # Create json directory if it doesn't exist
        json_dir = os.path.join("src", "json")
        os.makedirs(json_dir, exist_ok=True)
        
        # Use os.path.join for proper path handling
        file_path = os.path.join(json_dir, f"{wallet.id}.json")
        wallet.save_seed(file_path, encrypt=True)
        
        return {"success": True, "address": address.address_id, "wallet_id": wallet.id, "network_id": wallet.network_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

def call_contract_function(wallet: WalletType, function_name: str, function_args: dict):
    try:
        Cdp.configure_from_json("src/utils/cdp_api_key.json")
        user_wallet = Wallet.fetch(wallet.wallet_id)
        filePath = "src/json/" + wallet.wallet_id + ".json"
        user_wallet.load_seed(filePath)
        invocation = user_wallet.invoke_contract(
            contract_address=ERC20R_ADDRESS,
            abi=ERC20R_ABI,
            method=function_name,
            args=function_args
        )
        invocation.wait()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def call_governance_function(wallet: WalletType, function_name: str, function_args: dict):
    try:
        Cdp.configure_from_json("src/utils/cdp_api_key.json")
        user_wallet = Wallet.fetch(wallet.wallet_id)
        filePath = "src/json/" + wallet.wallet_id + ".json"
        user_wallet.load_seed(filePath)
        invocation = user_wallet.invoke_contract(
            contract_address=GOVERNANCE_ADDRESS,
            abi=GOVERNANCE_ABI,
            method=function_name,
            args=function_args
        )
        invocation.wait()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
def read_contract_function(wallet: WalletType, function_name: str, function_args: dict):
    try:
        Cdp.configure_from_json("src/utils/cdp_api_key.json")
        user_wallet = Wallet.fetch(wallet.wallet_id)
        filePath = "src/json/" + wallet.wallet_id + ".json"
        user_wallet.load_seed(filePath)
        
        uint16 = SmartContract.read(
            wallet.network_id,
            ERC20R_ADDRESS,
            function_name,
            ERC20R_ABI,
            function_args
        )
        return {"success": True, "result": uint16}
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_governance_function(wallet: WalletType, function_name: str, function_args: dict):
    try:
        Cdp.configure_from_json("src/utils/cdp_api_key.json")
        user_wallet = Wallet.fetch(wallet.wallet_id)
        filePath = "src/json/" + wallet.wallet_id + ".json"
        user_wallet.load_seed(filePath)
        
        uint16 = SmartContract.read(
            wallet.network_id,
            GOVERNANCE_ADDRESS,
            function_name,
            GOVERNANCE_ABI,
            function_args
        )
        return {"success": True, "result": uint16}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
# def read_governance_bool_function(wallet: WalletType, function_name: str, function_args: dict):
#     try:
#         Cdp.configure_from_json("src/utils/cdp_api_key.json")
#         user_wallet = Wallet.fetch(wallet.wallet_id)
#         filePath = "src/json/" + wallet.wallet_id + ".json"
#         user_wallet.load_seed(filePath)
        
#         uint16 = SmartContract.read(
#             wallet.network_id,
#             GOVERNANCE_ADDRESS,
#             function_name,
#             GOVERNANCE_ABI,
#             function_args
#         )
#         return {"success": True, "result": uint16}
#     except Exception as e:
#         return {"success": False, "error": str(e)}