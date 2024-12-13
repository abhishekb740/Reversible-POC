from cdp import *
from src.config.env import Env

api_key_name = Env.COINBASE_API_KEY_NAME
api_key_private_key = Env.COINBASE_API_KEY_SECRET

Cdp.configure_from_json("cdp_api_key.json")

wallet = Wallet.create()
address = wallet.default_address

print(address)
