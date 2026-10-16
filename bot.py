import os
from decimal import Decimal

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

rpc_url = os.getenv("MAINNET_RPC_URL")

w3 = Web3(Web3.HTTPProvider(rpc_url))

if not w3.is_connected():
    raise RuntimeError("Could not connect to Ethereum")


WETH = Web3.to_checksum_address(
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
)

USDC = Web3.to_checksum_address(
    "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
)

UNISWAP_FACTORY = Web3.to_checksum_address(
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
)


FACTORY_ABI = [
    {
        "inputs": [
            {"name": "tokenA", "type": "address"},
            {"name": "tokenB", "type": "address"},
        ],
        "name": "getPair",
        "outputs": [
            {"name": "pair", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [
            {"name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


factory = w3.eth.contract(
    address=UNISWAP_FACTORY,
    abi=FACTORY_ABI
)

pair_address = factory.functions.getPair(
    WETH,
    USDC
).call()

pair_address = Web3.to_checksum_address(pair_address)

pair = w3.eth.contract(
    address=pair_address,
    abi=PAIR_ABI
)

reserve0, reserve1, _ = pair.functions.getReserves().call()

token0 = pair.functions.token0().call()


if token0.lower() == USDC.lower():

    reserve_usdc = Decimal(reserve0) / Decimal(10**6)

    reserve_weth = Decimal(reserve1) / Decimal(10**18)

else:

    reserve_weth = Decimal(reserve0) / Decimal(10**18)

    reserve_usdc = Decimal(reserve1) / Decimal(10**6)


eth_price = reserve_usdc / reserve_weth


print()
print("Connected to Ethereum")
print("Current block:", w3.eth.block_number)

print()
print("Uniswap V2 WETH/USDC")
print("Pool address:", pair_address)

print()
print(f"ETH price: ${eth_price:,.2f}")

print()
print(f"WETH liquidity: {reserve_weth:,.2f}")
print(f"USDC liquidity: ${reserve_usdc:,.2f}")