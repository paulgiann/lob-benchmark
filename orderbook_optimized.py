import heapq


class OptimizedOrderBook:
    """Optimized limit order book.

    Key idea: avoid full re-sorts and avoid scanning large lists on delete.

    Structures:
      - orders_by_id: order_id -> order dict (O(1) average lookup)
      - bid_levels / ask_levels: price -> {order_id -> order dict}
        * fetching a price level is O(1) (plus O(k) to iterate k orders)
        * delete within a price level is O(1) average
      - bid_heap / ask_heap: heaps of prices for best bid/ask with lazy cleanup
        * stale price entries are popped when querying best bid/ask

    Note: prices are treated as hashable keys. In production you would typically
    use integer ticks (e.g., cents) or Decimal rather than raw floats.
    """

    def __init__(self):
        # 1) Lookup by order ID
        self.orders_by_id = {}

        # 2) Price levels (price -> {order_id: order_dict})
        self.bid_levels = {}
        self.ask_levels = {}

        # 3) Heaps for best prices (lazy stale cleanup)
        self.bid_heap = []  # store -price to simulate a max-heap
        self.ask_heap = []  # store +price as a min-heap

    def add_order(self, order):
        oid = order["order_id"]
        price = order["price"]
        side = order["side"]

        # Store canonical reference
        self.orders_by_id[oid] = order

        if side == "bid":
            level = self.bid_levels.get(price)
            if level is None:
                level = {}
                self.bid_levels[price] = level
                heapq.heappush(self.bid_heap, -price)
            level[oid] = order
        else:
            level = self.ask_levels.get(price)
            if level is None:
                level = {}
                self.ask_levels[price] = level
                heapq.heappush(self.ask_heap, price)
            level[oid] = order

    def amend_order(self, order_id, new_quantity):
        order = self.orders_by_id.get(order_id)
        if order is None:
            return False
        order["quantity"] = new_quantity
        return True

    def delete_order(self, order_id):
        order = self.orders_by_id.pop(order_id, None)
        if order is None:
            return False

        price = order["price"]
        side = order["side"]

        if side == "bid":
            level = self.bid_levels.get(price)
            if level is not None:
                level.pop(order_id, None)
                if len(level) == 0:
                    # Remove empty price level. Heap is cleaned lazily.
                    del self.bid_levels[price]
        else:
            level = self.ask_levels.get(price)
            if level is not None:
                level.pop(order_id, None)
                if len(level) == 0:
                    del self.ask_levels[price]

        return True

    # ---- required queries ----

    def lookup_by_id(self, order_id):
        return self.orders_by_id.get(order_id, None)

    def orders_at_price(self, price):
        # Match NaiveOrderBook API: return orders at this price on both sides
        bids = list(self.bid_levels.get(price, {}).values())
        asks = list(self.ask_levels.get(price, {}).values())
        return bids + asks

    def best_bid_ask(self):
        # Best bid (max price): pop stale prices until top corresponds to a non-empty level
        best_bid = None
        while self.bid_heap:
            price = -self.bid_heap[0]
            level = self.bid_levels.get(price)
            if level:
                best_bid = next(iter(level.values()))
                break
            heapq.heappop(self.bid_heap)

        # Best ask (min price)
        best_ask = None
        while self.ask_heap:
            price = self.ask_heap[0]
            level = self.ask_levels.get(price)
            if level:
                best_ask = next(iter(level.values()))
                break
            heapq.heappop(self.ask_heap)

        return best_bid, best_ask
