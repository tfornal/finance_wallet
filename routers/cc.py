from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()
coins = [
    "usdt",
    "ethereum",
    "bitcoin",
    "polkadot",
    "chainlink",
    "hadera",
    "flow",
    "yield-app",
    "mantle",
    "pepebrc",
    "pepe",
    "memecoin",
    "revenue-coin",
    "waves-exchange",
]
prices = cg.get_price(ids=coins, vs_currencies="usd")
print(prices)
