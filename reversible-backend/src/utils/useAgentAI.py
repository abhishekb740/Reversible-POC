from langchain_openai import ChatOpenAI
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
import requests
import os


probabilitySystemPrompt = """You are an agent, and based on evidence that a particular transaction was accidental or not, you have to determine if the transaction is accidental or not. If the transaction was accidental, return 1, else, return 2."""

probabilityUserPrompt = """Based on the following evidence:
{evidence}
Return the verdict, whether the transaction is accidental or not. If it is accidental, return 1, else return 2. Only return this, and nothing else."""


fraudulentCheckPrompt = """Objective: Determine Transaction Accidental Probability

Comprehensive Analysis Framework:
1. Transaction Verification
- Analyze transaction details from provided data
- Compute address mismatch significance - if the addresses are significantly different (more than 4 mismatches), then this transaction was likely not accidental. Do not compute this mismatch on your own, this will be provided to you.

2. Sender's Transaction Context
- Examine sender's transaction summary - check for fishy transaction summary
- Review sender's transaction history - check for fishy transaction history
- Identify anomalies or consistent patterns

3. Receiver's Transaction Context
- Analyze receiver's transaction summary - check for fishy transaction summary
- Review receiver's transaction history - check for fishy transaction history
- Detect potential suspicious interaction patterns

4. Claim Credibility Assessment
- Evaluate written proof's technical and narrative credibility - this is also a very important factor to deciding if a transaction was accidental or not. If the reason is convincing enough, the transaction was likely accidental.
- Cross-reference proof against transaction metadata
- Assess consistency and plausibility of accidental claim

Evaluation Methodology:
- Assign weighted probability based on:
  * Address similarity/mismatch - this will be computed and given to you, DO NOT DETERMINE THIS ON YOUR OWN
  * Transaction history consistency
  * Claim's detailed explanation
  * Historical transaction behavior

Decision Criteria:
- Provide single probabilistic output between 1 and 2
- Focus exclusively on accidental transaction likelihood
- Base probability on empirical evidence
- Exclude subjective interpretation

Output Constraint:
- Return if the transaction was accidental or not, with detailed reasoning as well for the same."""

fraudulentCheckInput = """Here are the details of the transaction. You must determine if the transaction was accidental or not.

Here is the amount of the transaction: {amount}

Here is the sender's transaction summary:
{senderTransactionSummary}

Here is the sender's transaction history:
{senderTransactionHistory}

Here is the receiver's transaction summary:
{receiverTransactionSummary}

Here is the sender's transaction history:
{receiverTransactionHistory}

Here is the sender's wallet address: {senderWalletAddress}
Here is the receiver's wallet address: {receiverWalletAddress}
Here is the intended recipient's wallet address: {intendedRecepientWalletAddress}
Hence the accurate number of mismatches that I have computed, between the actual recipient's wallet address and the intended recipient's wallet address is : {mismatches}

Here is the written proof from the sender to reverse the transaction in order to prove that the transaction was accidental: {writtenProofTitle}: {writtenProofContent}

Based on all the above details, tell if the transaction was accidental or not, and provide good reasoning as to why or why not."""


def countMismatches(wallet1: str, wallet2: str) -> int : 
    pointer1, pointer2 = 0, 0
    mismatches = 0

    while pointer1 < len(wallet1) and pointer2 < len(wallet2):
        if wallet1[pointer1] != wallet2[pointer2]:
            mismatches += 1
        pointer1 += 1
        pointer2 += 1

    return mismatches


def getTransactionSummary(chainName: str, walletAddress: str):
  url = "https://api.covalenthq.com/v1/{chainName}/address/{walletAddress}/transactions_summary/".format(chainName=chainName, walletAddress=walletAddress)
  querystring = {"with-gas":"true"}
  response = requests.request("GET", url, params=querystring, headers={'Authorization': 'Bearer {token}'.format(token=os.getenv("GOLDRUSH_API_KEY"))})

  return response.json()


def getTransactionHistory(chainName: str, walletAddress: str):
  url = "https://api.covalenthq.com/v1/{chainName}/address/{walletAddress}/transactions_v3/".format(chainName=chainName, walletAddress=walletAddress)
  response = requests.request("GET", url, headers={'Authorization': 'Bearer {token}'.format(token=os.getenv("GOLDRUSH_API_KEY"))})

  return response.json()


# def getTransaction(chainName: str, txHash: str):
#   url = "https://api.covalenthq.com/v1/{chainName}/transaction_v2/{txHash}/".format(chainName=chainName, txHash=txHash)
#   response = requests.request("GET", url, headers={'Authorization': 'Bearer {token}'.format(token=os.getenv("GOLDRUSH_API_KEY"))})
  
#   return response.json()


def initialize_agent():
  llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
  cdp = CdpAgentkitWrapper(cdp_api_key_name=os.getenv("CDP_API_KEY_NAME"), cdp_api_key_private_key=os.getenv("CDP_API_KEY_PRIVATE_KEY"))
  cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(cdp)
  tools = cdp_toolkit.get_tools()
  agent_executor = create_react_agent(
    llm,
    tools=tools,
    state_modifier="You are a helpful agent that can interact with the Base blockchain using CDP AgentKit. You can create wallets, deploy tokens, and perform transactions."
  )
  return agent_executor


def useAgent(agentExecutor: any, systemPrompt: str, inputPrompt: str):
  for chunk in agentExecutor.stream(
        {"messages": [AIMessage(content=systemPrompt), HumanMessage(content=inputPrompt)]},
        {"configurable": {"thread_id": "my_first_agent"}}
    ):
        if "agent" in chunk:
            output = chunk["agent"]["messages"][0].content
            return output
        elif "tools" in chunk:
            output = chunk["tools"]["messages"][0].content
            return output


def agentVerdict(agentExecutor: any, amount: int, senderWalletAddress: str, receiverWalletAddress: str, chainName: str, writtenProofTitle: str, writtenProofContent: str, intendedRecepientWalletAddress: str):
  senderTransactionHistory = getTransactionHistory(chainName=chainName, walletAddress=senderWalletAddress)
  receiverTransactionHistory = getTransactionHistory(chainName=chainName, walletAddress=receiverWalletAddress)
  
  senderTransactionSummary = getTransactionSummary(chainName=chainName, walletAddress=senderWalletAddress)
  receiverTransactionSummary = getTransactionSummary(chainName=chainName, walletAddress=receiverWalletAddress)

  mismatches = countMismatches(senderWalletAddress, receiverWalletAddress)
  
  systemPrompt = fraudulentCheckPrompt
  inputPrompt = fraudulentCheckInput.format(senderTransactionHistory=senderTransactionHistory, amount=amount, receiverTransactionHistory=receiverTransactionHistory, senderTransactionSummary=senderTransactionSummary, receiverTransactionSummary=receiverTransactionSummary, senderWalletAddress=senderWalletAddress, receiverWalletAddress=receiverWalletAddress, writtenProofTitle=writtenProofTitle, writtenProofContent=writtenProofContent, intendedRecepientWalletAddress=intendedRecepientWalletAddress, mismatches=mismatches)
  
  response = useAgent(agentExecutor=agentExecutor, systemPrompt=systemPrompt, inputPrompt=inputPrompt)
  
  return response


def agentVerdictProbability(agentExecutor: any, agentVerdict: str):
  systemPrompt = probabilitySystemPrompt
  userPrompt = probabilityUserPrompt.format(evidence=agentVerdict)
  response = useAgent(agentExecutor=agentExecutor, systemPrompt=systemPrompt, inputPrompt=userPrompt)
  
  return response




def useAIJudge(chainName: any, amount: int, senderAddress: str, receiverAddress: str, intendedRecipientWalletAddress: str, writtenProofTitle: str, writtenProofContent: str):
  agentExecutor = initialize_agent()
  agentResponse = agentVerdict(agentExecutor=agentExecutor, amount=amount, senderWalletAddress=senderAddress, receiverWalletAddress=receiverAddress, chainName=chainName, intendedRecepientWalletAddress=intendedRecipientWalletAddress, writtenProofTitle=writtenProofTitle, writtenProofContent=writtenProofContent)
  
  verdict = agentVerdictProbability(agentExecutor=agentExecutor, agentVerdict=agentResponse)
  print("verdict is : ", verdict)
  return verdict
