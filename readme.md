# Retrace - Decentralized Transaction Reversal Protocol

Retrace is a decentralized protocol that enables reversible transactions on EVM-compatible blockchains, providing users with a safety net against accidental transfers and fraud.

## Overview

Retrace introduces a novel approach to blockchain transactions by implementing:

- Reversible token transfers with a time-locked dispute period
- Decentralized dispute resolution through AI and human judges
- Fair governance system for managing disputes and protocol updates
- User-friendly interface for managing transactions and disputes

## Architecture

### Smart Contracts (`reversible-contract/`)
- `ERC20R.sol`: Extended ERC20 implementation with reversible transaction functionality
- `JudgeManager.sol`: Handles dispute resolution and judge management
- `Governance.sol`: Protocol governance and voting mechanisms

### Backend (`reversible-backend/`)
Built with FastAPI and Python, providing:
- Transaction management
- Dispute handling
- AI-powered initial dispute assessment
- User authentication and wallet management
- Integration with Supabase for data persistence

### Frontend (`reversible-client/`)
Next.js application offering:
- Intuitive transaction interface
- Dispute management dashboard
- Real-time transaction status tracking
- Wallet integration and balance management

## Key Features

1. **Reversible Transactions**
   - Time-locked period for dispute initiation
   - Automated and manual dispute resolution
   - Transaction history tracking

2. **AI-Powered Dispute Resolution**
   - Initial automated assessment of disputes
   - Pattern recognition for fraudulent activities
   - Support for human judge decision-making

3. **Decentralized Governance**
   - Community-driven dispute resolution
   - Transparent voting mechanism
   - Judge selection and management

## Technology Stack

- **Smart Contracts**: Solidity - Smart Contract deployed on Base.
- **Backend**: 
  - CDP SDK
  - Coinbase AgentKit
  - FastAPI
  - Python
  - Supabase
- **Frontend**:
  - Next.js
  - Coinbase OnchainKit
  - TypeScript
  - TailwindCSS
  - Web3 integration
