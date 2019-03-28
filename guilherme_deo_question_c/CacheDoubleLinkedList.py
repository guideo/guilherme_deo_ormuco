import gc


class Node:
    def __init__(self, prev_node=None, next_node=None, data=None):
        self.prev_node = prev_node
        self.next_node = next_node
        self.data = data


class CacheDoubleLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        self.max_size = 3

    def delete_last(self):
        self.size -= 1
        deleted_data = self.tail.data
        self.tail = self.tail.prev_node
        self.tail.next_node = None
        gc.collect()
        return deleted_data

    def hit(self, node):
        if node == self.head:
            return

        node.prev_node.next_node = node.next_node
        if node != self.tail:
            node.next_node.prev_node = node.prev_node
        else:
            self.tail = self.tail.prev_node
        node.next_node = self.head
        self.head.prev_node = node
        node.prev_node = None
        self.head = node

    def fault(self, node):
        # If list is full
        removed = None
        if self.size >= self.max_size:
            removed = self.delete_last()
            node.next_node = self.head
            self.head.prev_node = node
        # If list is empty
        elif self.size == 0:
            self.tail = node
        # Any other case
        else:
            node.next_node = self.head
            self.head.prev_node = node
        self.size += 1
        self.head = node
        return removed

    def __str__(self):
        traverse = self.head
        output = ''
        while traverse:
            output += str(traverse.data)
            if traverse != self.tail:
                output += ' <---> '
            traverse = traverse.next_node
        return output