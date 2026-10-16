import os
import csv
import time

from datetime import datetime, timezone
from decimal import Decimal, getcontext

from dotenv import load_dotenv
from web3 import Web3


# ==================================================
# SETUP
# ==================================================

getcontext().prec = 50

load_dotenv()

RPC_URL = os.getenv("MAINNET_RPC_URL")

if not RPC_URL:
    raise RuntimeError("MAINNET_RPC_URL not found in .env")


w3 = Web3(
    Web3.HTTPProvider(RPC_URL)
)


if not w3.is_connected():
    raise RuntimeError(
        "Could not connect to Ethereum"
    )


# ==================================================
# TOKENS
# ==================================================

TOKENS = {

    "WETH": {
        "address": Web3.to_checksum_address(
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        ),
        "decimals": 18
    },

    "USDC": {
        "address": Web3.to_checksum_address(
            "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        ),
        "decimals": 6
    },

    "WBTC": {
        "address": Web3.to_checksum_address(
            "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
        ),
        "decimals": 8
    },

    "LINK": {
        "address": Web3.to_checksum_address(
            "0x514910771AF9Ca656af840dff83E8264EcF986CA"
        ),
        "decimals": 18
    },

    "UNI": {
        "address": Web3.to_checksum_address(
            "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
        ),
        "decimals": 18
    },

    "DAI": {
        "address": Web3.to_checksum_address(
            "0x6B175474E89094C44Da98b954EedeAC495271d0F"
        ),
        "decimals": 18
    }
}


# ==================================================
# MARKETS
# ==================================================

MARKETS = [

    {
        "pair": "WETH/USDC",
        "base": "WETH",
        "quote": "USDC"
    },

    {
        "pair": "WBTC/WETH",
        "base": "WBTC",
        "quote": "WETH"
    },

    {
        "pair": "LINK/WETH",
        "base": "LINK",
        "quote": "WETH"
    },

    {
        "pair": "UNI/WETH",
        "base": "UNI",
        "quote": "WETH"
    },

    {
        "pair": "DAI/USDC",
        "base": "DAI",
        "quote": "USDC"
    }
]


# ==================================================
# DEX FACTORIES
# ==================================================

DEXES = {

    "Uniswap V2": Web3.to_checksum_address(
        "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
    ),

    "SushiSwap V2": Web3.to_checksum_address(
        "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"
    )
}


ZERO_ADDRESS = (
    "0x0000000000000000000000000000000000000000"
)


# ==================================================
# CONTRACT ABIS
# ==================================================

FACTORY_ABI = [
    {
        "inputs": [
            {
                "name": "tokenA",
                "type": "address"
            },
            {
                "name": "tokenB",
                "type": "address"
            }
        ],
        "name": "getPair",
        "outputs": [
            {
                "name": "pair",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


PAIR_ABI = [

    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [

            {
                "name": "_reserve0",
                "type": "uint112"
            },

            {
                "name": "_reserve1",
                "type": "uint112"
            },

            {
                "name": "_blockTimestampLast",
                "type": "uint32"
            }
        ],

        "stateMutability": "view",
        "type": "function"
    },

    {
        "inputs": [],
        "name": "token0",

        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ],

        "stateMutability": "view",
        "type": "function"
    }
]


# ==================================================
# TRADE SIZES
# ==================================================

TRADE_SIZES_USD = [

    100,
    250,
    500,
    1000,
    2000,
    5000,
    10000,
    20000,
    50000
]


ESTIMATED_GAS_UNITS = Decimal(
    300000
)


# ==================================================
# CREATE POOL OBJECT
# ==================================================

def create_pool(
    factory_address,
    base_symbol,
    quote_symbol
):

    base = TOKENS[base_symbol]
    quote = TOKENS[quote_symbol]

    factory = w3.eth.contract(
        address=factory_address,
        abi=FACTORY_ABI
    )

    pair_address = factory.functions.getPair(
        base["address"],
        quote["address"]
    ).call()

    if (
        pair_address.lower()
        == ZERO_ADDRESS.lower()
    ):
        return None

    pair_address = Web3.to_checksum_address(
        pair_address
    )

    contract = w3.eth.contract(
        address=pair_address,
        abi=PAIR_ABI
    )

    token0 = contract.functions.token0().call()

    base_is_token0 = (
        token0.lower()
        == base["address"].lower()
    )

    return {

        "address": pair_address,

        "contract": contract,

        "base": base_symbol,

        "quote": quote_symbol,

        "base_is_token0": base_is_token0
    }


# ==================================================
# INITIALISE MARKETS
# ==================================================

def initialise_markets():

    active_markets = []

    print()
    print("Initialising pools...")
    print()

    for market in MARKETS:

        pools = {}

        valid = True

        for dex_name, factory in DEXES.items():

            pool = create_pool(
                factory,
                market["base"],
                market["quote"]
            )

            if pool is None:

                print(
                    f"Skipping {market['pair']} "
                    f"because no {dex_name} pool exists."
                )

                valid = False

                break

            pools[dex_name] = pool

        if valid:

            active_markets.append({

                **market,

                "pools": pools
            })

            print(
                f"Loaded {market['pair']}"
            )

    print()

    return active_markets


ACTIVE_MARKETS = initialise_markets()


if len(ACTIVE_MARKETS) == 0:

    raise RuntimeError(
        "No usable markets found."
    )


# ==================================================
# READ POOL RESERVES
# ==================================================

def read_pool(pool):

    reserve0, reserve1, _ = (
        pool["contract"]
        .functions
        .getReserves()
        .call()
    )

    base_symbol = pool["base"]
    quote_symbol = pool["quote"]

    base_decimals = (
        TOKENS[base_symbol]["decimals"]
    )

    quote_decimals = (
        TOKENS[quote_symbol]["decimals"]
    )


    if pool["base_is_token0"]:

        base_raw = reserve0

        quote_raw = reserve1

    else:

        base_raw = reserve1

        quote_raw = reserve0


    base_reserve = (
        Decimal(base_raw)
        / Decimal(
            10 ** base_decimals
        )
    )

    quote_reserve = (
        Decimal(quote_raw)
        / Decimal(
            10 ** quote_decimals
        )
    )


    price = (
        quote_reserve
        / base_reserve
    )


    return {

        "price": price,

        "base_raw": base_raw,

        "quote_raw": quote_raw,

        "base_reserve": base_reserve,

        "quote_reserve": quote_reserve
    }


# ==================================================
# AMM MATHS
# ==================================================

def amount_out(
    amount_in,
    reserve_in,
    reserve_out
):

    # 0.3% V2 fee

    amount_in_with_fee = (
        amount_in * 997
    )

    numerator = (
        amount_in_with_fee
        * reserve_out
    )

    denominator = (
        reserve_in * 1000
        + amount_in_with_fee
    )

    return (
        numerator
        // denominator
    )


# ==================================================
# SIMULATE ARBITRAGE
# ==================================================

def simulate_route(
    starting_quote,
    buy_pool,
    sell_pool,
    quote_symbol
):

    quote_decimals = (
        TOKENS[quote_symbol]["decimals"]
    )

    starting_raw = int(
        starting_quote
        * Decimal(
            10 ** quote_decimals
        )
    )


    # ----------------------------------------------
    # Buy base token using quote token
    # ----------------------------------------------

    base_received = amount_out(

        starting_raw,

        buy_pool["quote_raw"],

        buy_pool["base_raw"]
    )


    # ----------------------------------------------
    # Sell base token back into quote token
    # ----------------------------------------------

    final_quote_raw = amount_out(

        base_received,

        sell_pool["base_raw"],

        sell_pool["quote_raw"]
    )


    final_quote = (

        Decimal(final_quote_raw)

        / Decimal(
            10 ** quote_decimals
        )
    )


    return (
        final_quote
        - starting_quote
    )


# ==================================================
# USD CONVERSION
# ==================================================

def usd_to_quote(
    usd_amount,
    quote_symbol,
    eth_price_usd
):

    usd_amount = Decimal(
        str(usd_amount)
    )

    if quote_symbol == "USDC":

        return usd_amount

    if quote_symbol == "WETH":

        return (
            usd_amount
            / eth_price_usd
        )

    raise ValueError(
        f"No USD conversion for {quote_symbol}"
    )


def quote_profit_to_usd(
    amount,
    quote_symbol,
    eth_price_usd
):

    if quote_symbol == "USDC":

        return amount

    if quote_symbol == "WETH":

        return (
            amount
            * eth_price_usd
        )

    raise ValueError(
        f"No USD conversion for {quote_symbol}"
    )


# ==================================================
# FIND BEST TRADE
# ==================================================

def find_best_trade(
    quote_symbol,
    uni,
    sushi,
    eth_price_usd,
    gas_cost_usd
):

    best_profit_usd = Decimal(
        "-999999999"
    )

    best_size_usd = 0

    best_route = "NO TRADE"


    for size_usd in TRADE_SIZES_USD:

        starting_quote = usd_to_quote(

            size_usd,

            quote_symbol,

            eth_price_usd
        )


        # ------------------------------------------
        # Uniswap -> SushiSwap
        # ------------------------------------------

        profit_quote_1 = simulate_route(

            starting_quote,

            uni,

            sushi,

            quote_symbol
        )


        profit_usd_1 = (

            quote_profit_to_usd(

                profit_quote_1,

                quote_symbol,

                eth_price_usd
            )

            - gas_cost_usd
        )


        # ------------------------------------------
        # SushiSwap -> Uniswap
        # ------------------------------------------

        profit_quote_2 = simulate_route(

            starting_quote,

            sushi,

            uni,

            quote_symbol
        )


        profit_usd_2 = (

            quote_profit_to_usd(

                profit_quote_2,

                quote_symbol,

                eth_price_usd
            )

            - gas_cost_usd
        )


        if profit_usd_1 > best_profit_usd:

            best_profit_usd = (
                profit_usd_1
            )

            best_size_usd = (
                size_usd
            )

            best_route = (
                "Uniswap -> SushiSwap"
            )


        if profit_usd_2 > best_profit_usd:

            best_profit_usd = (
                profit_usd_2
            )

            best_size_usd = (
                size_usd
            )

            best_route = (
                "SushiSwap -> Uniswap"
            )


    # ----------------------------------------------
    # Never recommend trading a losing opportunity
    # ----------------------------------------------

    if best_profit_usd <= 0:

        signal = "NO TRADE"

        trade_size_usd = 0

    else:

        signal = "TRADE"

        trade_size_usd = (
            best_size_usd
        )


    return {

        "signal": signal,

        "route": best_route,

        "trade_size_usd": (
            trade_size_usd
        ),

        "candidate_size_usd": (
            best_size_usd
        ),

        "net_pnl_usd": (
            best_profit_usd
        )
    }


# ==================================================
# OUTPUT FILE
# ==================================================

os.makedirs(
    "data",
    exist_ok=True
)


CSV_FILE = (
    "data/multi_market_log.csv"
)


HEADER = [

    "timestamp",

    "block",

    "pair",

    "base",

    "quote",

    "uniswap_price",

    "sushiswap_price",

    "spread_percent",

    "gas_gwei",

    "signal",

    "best_route",

    "trade_size_usd",

    "candidate_size_usd",

    "best_net_pnl_usd"
]


if not os.path.exists(CSV_FILE):

    with open(
        CSV_FILE,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            HEADER
        )


# ==================================================
# MAIN LOGGER
# ==================================================

print()
print("MULTI MARKET ARBITRAGE SCANNER")
print("==============================")
print()
print(
    f"Tracking {len(ACTIVE_MARKETS)} markets"
)
print()
print(
    "Press Ctrl + C to stop."
)
print()


last_block = None


try:

    while True:

        current_block = (
            w3.eth.block_number
        )


        if current_block == last_block:

            time.sleep(2)

            continue


        last_block = current_block


        # ------------------------------------------
        # Read every market
        # ------------------------------------------

        snapshots = {}


        for market in ACTIVE_MARKETS:

            pair_name = (
                market["pair"]
            )


            uni = read_pool(

                market["pools"][
                    "Uniswap V2"
                ]
            )


            sushi = read_pool(

                market["pools"][
                    "SushiSwap V2"
                ]
            )


            snapshots[pair_name] = {

                "market": market,

                "uni": uni,

                "sushi": sushi
            }


        # ------------------------------------------
        # ETH / USD reference
        # ------------------------------------------

        if "WETH/USDC" not in snapshots:

            raise RuntimeError(
                "WETH/USDC required "
                "for USD conversion."
            )


        eth_ref = snapshots[
            "WETH/USDC"
        ]


        eth_price_usd = (

            eth_ref["uni"]["price"]

            + eth_ref["sushi"]["price"]

        ) / Decimal(2)


        # ------------------------------------------
        # Gas
        # ------------------------------------------

        gas_wei = Decimal(
            w3.eth.gas_price
        )


        gas_gwei = (

            gas_wei

            / Decimal(
                10**9
            )
        )


        gas_cost_eth = (

            ESTIMATED_GAS_UNITS

            * gas_wei

            / Decimal(
                10**18
            )
        )


        gas_cost_usd = (

            gas_cost_eth

            * eth_price_usd
        )


        timestamp = datetime.now(
            timezone.utc
        ).isoformat()


        print()
        print(
            f"Block {current_block}"
        )

        print(
            f"ETH: ${eth_price_usd:,.2f}"
        )

        print(
            f"Gas: {gas_gwei:.3f} Gwei "
            f"(~${gas_cost_usd:.2f})"
        )

        print(
            "-" * 70
        )


        # ------------------------------------------
        # Analyse every market
        # ------------------------------------------

        for pair_name, snapshot in (
            snapshots.items()
        ):

            market = (
                snapshot["market"]
            )

            uni = (
                snapshot["uni"]
            )

            sushi = (
                snapshot["sushi"]
            )


            spread = abs(

                uni["price"]

                - sushi["price"]
            )


            spread_percent = (

                spread

                / min(
                    uni["price"],
                    sushi["price"]
                )

                * Decimal(100)
            )


            result = find_best_trade(

                market["quote"],

                uni,

                sushi,

                eth_price_usd,

                gas_cost_usd
            )


            # --------------------------------------
            # Save
            # --------------------------------------

            with open(
                CSV_FILE,
                "a",
                newline=""
            ) as file:

                writer = csv.writer(file)

                writer.writerow([

                    timestamp,

                    current_block,

                    pair_name,

                    market["base"],

                    market["quote"],

                    float(
                        uni["price"]
                    ),

                    float(
                        sushi["price"]
                    ),

                    float(
                        spread_percent
                    ),

                    float(
                        gas_gwei
                    ),

                    result[
                        "signal"
                    ],

                    result[
                        "route"
                    ],

                    result[
                        "trade_size_usd"
                    ],

                    result[
                        "candidate_size_usd"
                    ],

                    float(
                        result[
                            "net_pnl_usd"
                        ]
                    )
                ])


            # --------------------------------------
            # Terminal display
            # --------------------------------------

            print(
                f"{pair_name:12} | "
                f"Spread "
                f"{spread_percent:.4f}% | "
                f"{result['signal']:8} | "
                f"Best P&L "
                f"${result['net_pnl_usd']:.2f}"
            )


        print(
            "-" * 70
        )


except KeyboardInterrupt:

    print()
    print(
        "Scanner stopped."
    )