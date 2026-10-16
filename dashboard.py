import os

import pandas as pd
import streamlit as st


# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(

    page_title=(
        "Multi Market DeFi Scanner"
    ),

    page_icon="📈",

    layout="wide"
)


LOG_FILE = (
    "data/multi_market_log.csv"
)


# ==================================================
# LOAD DATA
# ==================================================

@st.cache_data(ttl=3)
def load_history():

    if not os.path.exists(
        LOG_FILE
    ):

        return None

    try:

        df = pd.read_csv(
            LOG_FILE
        )

    except Exception:

        return None

    if len(df) == 0:

        return None

    df["timestamp"] = (
        pd.to_datetime(
            df["timestamp"]
        )
    )

    return df


# ==================================================
# HEADER
# ==================================================

st.title(
    "Multi Market DeFi Arbitrage Scanner"
)

st.caption(
    "Live Ethereum Mainnet analysis across "
    "Uniswap V2 and SushiSwap V2"
)


if st.button(
    "Refresh Dashboard"
):

    st.cache_data.clear()

    st.rerun()


history = load_history()


if history is None:

    st.warning(
        "No market data yet. "
        "Run logger.py first."
    )

    st.stop()


# ==================================================
# LATEST MARKET SNAPSHOT
# ==================================================

latest = (

    history

    .sort_values(
        "timestamp"
    )

    .groupby(
        "pair",
        as_index=False
    )

    .tail(1)

    .copy()
)


profitable_now = latest[
    latest["signal"]
    == "TRADE"
]


best_current_pnl = latest[
    "best_net_pnl_usd"
].max()


largest_current_spread = latest[
    "spread_percent"
].max()


# ==================================================
# TOP METRICS
# ==================================================

st.divider()


col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:

    st.metric(

        "Markets Tracked",

        len(latest)
    )


with col2:

    st.metric(

        "Profitable Now",

        len(
            profitable_now
        )
    )


with col3:

    st.metric(

        "Best Current P&L",

        f"${best_current_pnl:.2f}"
    )


with col4:

    st.metric(

        "Largest Spread",

        f"{largest_current_spread:.4f}%"
    )


# ==================================================
# TABS
# ==================================================

tab1, tab2, tab3 = st.tabs([

    "Live Markets",

    "Pair History",

    "Opportunities"
])


# ==================================================
# TAB 1
# ==================================================

with tab1:

    st.subheader(
        "Current Markets"
    )


    latest_display = latest[
        [

            "pair",

            "quote",

            "uniswap_price",

            "sushiswap_price",

            "spread_percent",

            "signal",

            "best_route",

            "trade_size_usd",

            "best_net_pnl_usd"
        ]
    ].copy()


    latest_display = (
        latest_display.sort_values(
            "best_net_pnl_usd",
            ascending=False
        )
    )


    # ----------------------------------------------
    # Format prices depending on quote currency
    # ----------------------------------------------

    def format_price(
        row,
        column
    ):

        value = row[column]

        if row["quote"] == "USDC":

            return (
                f"${value:,.4f}"
            )

        if row["quote"] == "WETH":

            return (
                f"{value:.8f} WETH"
            )

        return str(value)


    latest_display[
        "Uniswap Price"
    ] = latest_display.apply(

        lambda row: format_price(
            row,
            "uniswap_price"
        ),

        axis=1
    )


    latest_display[
        "SushiSwap Price"
    ] = latest_display.apply(

        lambda row: format_price(
            row,
            "sushiswap_price"
        ),

        axis=1
    )


    latest_display[
        "Spread"
    ] = latest_display[
        "spread_percent"
    ].map(

        lambda x: (
            f"{x:.4f}%"
        )
    )


    latest_display[
        "Trade Size"
    ] = latest_display[
        "trade_size_usd"
    ].map(

        lambda x: (
            f"${x:,.0f}"
        )
    )


    latest_display[
        "Net P&L"
    ] = latest_display[
        "best_net_pnl_usd"
    ].map(

        lambda x: (
            f"${x:,.2f}"
        )
    )


    final_table = latest_display[
        [

            "pair",

            "Uniswap Price",

            "SushiSwap Price",

            "Spread",

            "signal",

            "best_route",

            "Trade Size",

            "Net P&L"
        ]
    ]


    final_table.columns = [

        "Pair",

        "Uniswap",

        "SushiSwap",

        "Spread",

        "Signal",

        "Best Route",

        "Trade Size",

        "Net P&L"
    ]


    st.dataframe(

        final_table,

        use_container_width=True,

        hide_index=True
    )


    # ----------------------------------------------
    # Current signals
    # ----------------------------------------------

    st.divider()

    st.subheader(
        "Trading Signals"
    )


    if len(
        profitable_now
    ) == 0:

        st.info(
            "No profitable opportunities "
            "are currently detected."
        )

    else:

        for _, row in (
            profitable_now.iterrows()
        ):

            st.success(

                f"{row['pair']} | "
                f"{row['best_route']} | "
                f"Trade ${row['trade_size_usd']:,.0f} | "
                f"Estimated P&L "
                f"${row['best_net_pnl_usd']:.2f}"
            )


# ==================================================
# TAB 2
# ==================================================

with tab2:

    st.subheader(
        "Historical Analysis"
    )


    available_pairs = sorted(
        history["pair"]
        .unique()
    )


    selected_pair = (
        st.selectbox(

            "Select market",

            available_pairs
        )
    )


    pair_history = (

        history[

            history["pair"]
            == selected_pair

        ]

        .sort_values(
            "timestamp"
        )

        .copy()
    )


    if len(
        pair_history
    ) > 0:


        # ------------------------------------------
        # Summary metrics
        # ------------------------------------------

        total_observations = len(
            pair_history
        )


        profitable_signals = len(

            pair_history[

                pair_history[
                    "signal"
                ]
                == "TRADE"

            ]
        )


        max_spread = (
            pair_history[
                "spread_percent"
            ].max()
        )


        best_pnl = (
            pair_history[
                "best_net_pnl_usd"
            ].max()
        )


        c1, c2, c3, c4 = (
            st.columns(4)
        )


        with c1:

            st.metric(

                "Observations",

                f"{total_observations:,}"
            )


        with c2:

            st.metric(

                "Profitable Signals",

                f"{profitable_signals:,}"
            )


        with c3:

            st.metric(

                "Largest Spread",

                f"{max_spread:.4f}%"
            )


        with c4:

            st.metric(

                "Best P&L",

                f"${best_pnl:.2f}"
            )


        # ------------------------------------------
        # DEX prices
        # ------------------------------------------

        st.write(
            "### DEX Price Comparison"
        )


        price_chart = (

            pair_history[
                [

                    "timestamp",

                    "uniswap_price",

                    "sushiswap_price"
                ]
            ]

            .set_index(
                "timestamp"
            )
        )


        st.line_chart(
            price_chart
        )


        # ------------------------------------------
        # Spread
        # ------------------------------------------

        st.write(
            "### Spread History"
        )


        spread_chart = (

            pair_history[
                [

                    "timestamp",

                    "spread_percent"
                ]
            ]

            .set_index(
                "timestamp"
            )
        )


        st.line_chart(
            spread_chart
        )


        # ------------------------------------------
        # P&L
        # ------------------------------------------

        st.write(
            "### Best Simulated Net P&L"
        )


        pnl_chart = (

            pair_history[
                [

                    "timestamp",

                    "best_net_pnl_usd"
                ]
            ]

            .set_index(
                "timestamp"
            )
        )


        st.line_chart(
            pnl_chart
        )


        # ------------------------------------------
        # Recent observations
        # ------------------------------------------

        st.write(
            "### Recent Observations"
        )


        recent = (

            pair_history[

                [

                    "timestamp",

                    "block",

                    "spread_percent",

                    "signal",

                    "best_route",

                    "trade_size_usd",

                    "best_net_pnl_usd"
                ]

            ]

            .tail(30)

            .sort_values(
                "timestamp",
                ascending=False
            )
        )


        st.dataframe(

            recent,

            use_container_width=True,

            hide_index=True
        )


# ==================================================
# TAB 3
# ==================================================

with tab3:

    st.subheader(
        "Detected Opportunities"
    )


    opportunities = (

        history[

            history[
                "signal"
            ]
            == "TRADE"

        ]

        .sort_values(
            "best_net_pnl_usd",
            ascending=False
        )

        .copy()
    )


    if len(
        opportunities
    ) == 0:

        st.info(
            "No profitable signals have "
            "been recorded yet."
        )

    else:

        total_opportunities = len(
            opportunities
        )


        best_ever = (
            opportunities[
                "best_net_pnl_usd"
            ].max()
        )


        o1, o2 = st.columns(2)


        with o1:

            st.metric(

                "Signals Recorded",

                f"{total_opportunities:,}"
            )


        with o2:

            st.metric(

                "Best Recorded P&L",

                f"${best_ever:.2f}"
            )


        opportunity_table = (

            opportunities[
                [

                    "timestamp",

                    "block",

                    "pair",

                    "spread_percent",

                    "best_route",

                    "trade_size_usd",

                    "best_net_pnl_usd"
                ]
            ]

            .head(100)
        )


        st.dataframe(

            opportunity_table,

            use_container_width=True,

            hide_index=True
        )


# ==================================================
# FOOTER INFORMATION
# ==================================================

st.divider()


with st.expander(
    "How the scanner works"
):

    st.write(
        """
        The scanner reads liquidity pool reserves
        directly from Ethereum Mainnet.
        """
    )

    st.write(
        """
        It simulates both arbitrage directions
        between Uniswap V2 and SushiSwap V2.
        """
    )

    st.write(
        """
        Swap fees, price impact and an estimated
        gas cost are included before a signal is
        marked as profitable.
        """
    )

    st.write(
        """
        A TRADE signal is still only a simulation.
        It does not mean the opportunity could
        necessarily be executed before another
        market participant.
        """
    )