import heapq


class OptimizedOrderBook:
    def __init__(self):
        # 1) lookup by order id
        self.orders_by_id = {}

        # 2) price -> list of orders (we store dicts in a list)
        self.bid_levels = {}  # price -> list of orders
        self.ask_levels = {}  # price -> list of orders

        # 3) heaps to get best prices fast
        self.bid_heap = []  # store -price (max-heap via negatives)
        self.ask_heap = []  # store +price (min-heap)

        # keep counts so we can remove empty price levels lazily
        self.bid_level_count = {}  # price -> how many orders currently at this price
        self.ask_level_count = {}

    def add_order(self, order):
        oid = order["order_id"]
        price = order["price"]
        side = order["side"]

        self.orders_by_id[oid] = order

        if side == "bid":
            if price not in self.bid_levels:
                self.bid_levels[price] = []
                heapq.heappush(self.bid_heap, -price)
                self.bid_level_count[price] = 0
            self.bid_levels[price].append(order)
            self.bid_level_count[price] += 1

        else:
            if price not in self.ask_levels:
                self.ask_levels[price] = []
                heapq.heappush(self.ask_heap, price)
                self.ask_level_count[price] = 0
            self.ask_levels[price].append(order)
            self.ask_level_count[price] += 1

    def amend_order(self, order_id, new_quantity):
        if order_id not in self.orders_by_id:
            return False
        self.orders_by_id[order_id]["quantity"] = new_quantity
        return True

    def delete_order(self, order_id):
        if order_id not in self.orders_by_id:
            return False

        order = self.orders_by_id.pop(order_id)
        price = order["price"]
        side = order["side"]

        if side == "bid":
            # remove from the level list (scan only within that price level)
            level_list = self.bid_levels.get(price, [])
            for i in range(len(level_list)):
                if level_list[i]["order_id"] == order_id:
                    level_list.pop(i)
                    self.bid_level_count[price] -= 1
                    break

            # if empty, remove dict entry (heap cleanup is lazy)
            if self.bid_level_count.get(price, 0) == 0:
                if price in self.bid_levels:
                    del self.bid_levels[price]

        else:
            level_list = self.ask_levels.get(price, [])
            for i in range(len(level_list)):
                if level_list[i]["order_id"] == order_id:
                    level_list.pop(i)
                    self.ask_level_count[price] -= 1
                    break

            if self.ask_level_count.get(price, 0) == 0:
                if price in self.ask_levels:
                    del self.ask_levels[price]

        return True

    # ---- required queries ----

    def lookup_by_id(self, order_id):
        return self.orders_by_id.get(order_id, None)

    def orders_at_price(self, price, side=None):
        if side == "bid":
            return list(self.bid_levels.get(price, []))
        if side == "ask":
            return list(self.ask_levels.get(price, []))
        # both sides
        return list(self.bid_levels.get(price, [])) + list(self.ask_levels.get(price, []))

    def best_bid_ask(self):
        # best bid: pop stale prices until top is active
        best_bid = None
        while len(self.bid_heap) > 0:
            price = -self.bid_heap[0]
            if price in self.bid_levels and len(self.bid_levels[price]) > 0:
                best_bid = self.bid_levels[price][0]  # any order at best price
                break
            heapq.heappop(self.bid_heap)

        best_ask = None
        while len(self.ask_heap) > 0:
            price = self.ask_heap[0]
            if price in self.ask_levels and len(self.ask_levels[price]) > 0:
                best_ask = self.ask_levels[price][0]
                break
            heapq.heappop(self.ask_heap)

        return best_bid, best_ask
