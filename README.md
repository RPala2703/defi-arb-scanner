# DeFi Arbitrage Scanner

Read-only research tool that monitors Uniswap V2 markets on Ethereum mainnet for price discrepancies and logs them for analysis. It does not trade or hold keys.

## Features

- Queries on-chain Uniswap V2 pair reserves via `web3.py` (WETH, USDC, WBTC, LINK, UNI, DAI)
- Computes prices and spreads with `Decimal` precision
- `logger.py` records multi-market price history to CSV
- `dashboard.py` is a Streamlit dashboard that auto-refreshes from the logs

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install web3 python-dotenv pandas streamlit
cp .env.example .env   # add your Ethereum mainnet RPC URL
```

## Usage

```bash
python logger.py            # collect market data into data/
streamlit run dashboard.py  # view the dashboard
python bot.py               # single WETH/USDC pair price check
```

Sample logs are in `data/`.
