FLASK WEB APP THAT RECEIVES TRADINGVIEW ALERT WEBHOOKS

- ngrok, flask, sqllite, webhooks
- redis integration to interactive brokers (next step)

1 terminal ./ngrok http 80 :this will open specific network connection on port 80
2 VS terminal python app.py within terminal (specific port specified within main fnc)
3 copy https address from ngrok console window (this is your webhook)
4 paste into TV webhook alerts 
5 json message for strategies
6 make sure to start up postgres
7 check that redis is on if trying to hit IBrokers: redis-server redis-cli shutdown redis-cli ping



{
    "passphrase": "abcdefgh",
    "time": "{{timenow}}",
    "exchange": "{{exchange}}",
    "ticker": "{{ticker}}",
    "bar": {
        "time": "{{timenow}}",
        "open":"{{open}}",
        "high": "{{high}}",
        "low": "{{low}}",
        "close": "{{close}}",
        "volume": "{{volume}}"
    },
       "strategy": {
        "position_size": "{{strategy.position_size}}",
        "order_action": "{{strategy.order.action}}",
        "order_contracts": "{{strategy.order.contracts}}",
        "order_price": "{{strategy.order.price}}",
        "order_id": "{{strategy.order.id}}",
        "market_position": "{{strategy.market_position}}",
        "market_position_size": "{{strategy.market_position_size}}",
        "prev_market_position": "{{strategy.prev_market_position}}",
        "prev_market_position_size": "{{strategy.prev_market_position_size}}"
    }
}
