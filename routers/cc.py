import requests


# def get_crypto_price(coin):
#     url = "https://api.coingecko.com/api/v3/simple/price"
#     parameters = {
#         "ids": f"{coin}",
#         "vs_currencies": "usd",
#     }

#     response = requests.get(url, params=parameters)
#     data = response.json()

#     if coin in data and "usd" in data[coin]:/
#         crypto_price = data[coin]["usd"]
#         return crypto_price
#     else:
#         print(f"Error: Unable to fetch {coin} price.")
#         return None


# coins = [
#     "usdt",
#     "ethereum",
#     "bitcoin",
#     "polkadot",
#     "chainlink",
#     "hadera",
#     "hbar",
#     "flow",
#     "yield-app",
#     "mantle",
#     "pepebrc",
#     "pepe",
#     "memecoin",
#     "revenue-coin",
#     "waves-exchange",
# ]

# for coin in coins:
#     price = get_crypto_price(coin)

#     if price is not None:
#         print(f"The most recent price of {coin.capitalize()} is ${price:.2f} USD.")


# import requests


def get_bitcoin_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    parameters = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
    }

    response = requests.get(url, params=parameters)
    data = response.json()

    if "bitcoin" in data and "usd" in data["bitcoin"]:
        bitcoin_price = data["bitcoin"]["usd"]
        return bitcoin_price
    else:
        print("Error: Unable to fetch Bitcoin price.")
        return None


bitcoin_price = get_bitcoin_price()

if bitcoin_price is not None:
    print(f"The most recent price of Bitcoin is ${bitcoin_price:.2f} USD.")
