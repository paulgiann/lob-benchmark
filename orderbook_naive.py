class NaiveOrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []

    def add_order(self, order):
        if order["side"] == "bid":
            self.bids.append(order)
            self.bids.sort(key=lambda x: x["price"], reverse=True)
        else:
            self.asks.append(order)
            self.asks.sort(key=lambda x: x["price"])

    def amend_order(self, order_id, new_quantity):
        # scan bids
        for o in self.bids:
            if o["order_id"] == order_id:
                o["quantity"] = new_quantity
                self.bids.sort(key=lambda x: x["price"], reverse=True)
                return True

        # scan asks
        for o in self.asks:
            if o["order_id"] == order_id:
                o["quantity"] = new_quantity
                self.asks.sort(key=lambda x: x["price"])
                return True

        return False

    def delete_order(self, order_id):
        # scan bids
        for i in range(len(self.bids)):
            if self.bids[i]["order_id"] == order_id:
                self.bids.pop(i)
                self.bids.sort(key=lambda x: x["price"], reverse=True)
                return True

        # scan asks
        for i in range(len(self.asks)):
            if self.asks[i]["order_id"] == order_id:
                self.asks.pop(i)
                self.asks.sort(key=lambda x: x["price"])
                return True

        return False

    # ---- required queries ----

    def lookup_by_id(self, order_id):
        for o in self.bids:
            if o["order_id"] == order_id:
                return o
        for o in self.asks:
            if o["order_id"] == order_id:
                return o
        return None

    def orders_at_price(self, price):
        result = []
        for o in self.bids:
            if o["price"] == price:
                result.append(o)
        for o in self.asks:
            if o["price"] == price:
                result.append(o)
        return result

    def best_bid_ask(self):
        best_bid = self.bids[0] if len(self.bids) > 0 else None
        best_ask = self.asks[0] if len(self.asks) > 0 else None
        return best_bid, best_ask
