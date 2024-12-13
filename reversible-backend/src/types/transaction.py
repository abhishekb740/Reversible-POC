from pydantic import BaseModel
from typing import Optional

class DisputeRequest(BaseModel):
    transaction_id: str
    to_wallet: str
    proofTitle: str
    proofContent: str
class ReverseTransactionRequest(BaseModel):
    to_wallet: str
    transaction_id: str

class TransferRequest(BaseModel):
    to_wallet: str
    amount: str

class ForceApprovalRequest(BaseModel):
    transaction_id: str
    to_wallet: str
