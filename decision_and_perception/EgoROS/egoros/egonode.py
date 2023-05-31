from threading import Thread
from typing import Any, Dict, Callable, List
from .node import Node
from .pubsub import Message, MessageContext, Subscription, Topic
import multiprocessing
import sys
import time

# FIXME: add init call when reloading the node
class EgoNode:
    '''
    
    '''

    def __init__(self, node: Node, topics: Dict[str, Topic]) -> None:
        """
        Constructor for the EgoNode class
        @param node: The Node object
        @param topics: A dictionary of topics
        """
        self.inner_node = node
        self.running = False
        self.topics = topics
        self.subscriptions: Dict[str, Subscription] = {}
        self.pending_subscriptions: multiprocessing.Queue[str] = multiprocessing.Queue()
        pass

    def launch(self) -> Callable[[], None]:
        """
        Launches the EgoNode
        @return: A callable function to join the processes
        """
        # Initialize and get configuration
        # FIXME: if node crashes when initializing, the __tick thread still launches
        self.config = self.inner_node.init(self)

        self.running = True

        self.ticker_handler = None
        self.topic_reader_handler = multiprocessing.Process(target=self.__topic_reader_worker)
        self.topic_reader_handler.start()
        if self.inner_node.is_tickable():
            self.ticker_handler = multiprocessing.Process(target=self.__tick_handler)
            self.ticker_handler.start()

        def join():
            self.topic_reader_handler.join()
            if self.ticker_handler != None:
                self.ticker_handler.join()

        return join
            
    def stop(self):
        """
        Stops the EgoNode
        """
        self.running = False

    def subscribe(self, topic: str, callback: Callable[[Any, MessageContext], None]):
        """
        Subscribes to a topic with a callback function
        @param topic: The topic to subscribe to
        @param callback: The callback function to be triggered when a message is received
        """
        # TODO: move this to a better location

        # Check if topic already exists
        if not topic in self.topics:
            self.topics[topic] = Topic(
                name=topic
            )

        # Check if subscription context exists
        if not topic in self.subscriptions:
            self.subscriptions[topic] = Subscription()
            # Create new callback 
            cb = lambda msg, ctx: self.__enqueue_topic(topic, msg, ctx)
            self.topics[topic].subscribe(cb)
            self.pending_subscriptions.put(topic)

        self.subscriptions[topic].callbacks.append(callback)

    def __enqueue_topic(self, topic, msg, ctx):
        """
        Enqueues a message for a topic subscription
        @param topic: The topic
        @param msg: The message value
        @param ctx: The message context
        """
        print (self.subscriptions[topic].msg_queue)
        self.subscriptions[topic].msg_queue.put(Message(
            value=msg,
            ctx=ctx
        ))

    def publish(self, topic: str, value: Any):
        """
        Publishes a message to a topic
        @param topic: The topic to publish to
        @param value: The value to publish
        """
        if not topic in self.topics:
            self.topics[topic] = Topic(
                name=topic
            )

        self.topics[topic].publish(value)

    def __topic_subscription_worker(self, topic):
        """
        Worker function for handling topic subscriptions
        @param topic: The topic to handle
        """
        sub = self.subscriptions[topic]
        while (self.running):
            msg = sub.msg_queue.get()
            for callback in sub.callbacks:
                callback(
                    msg.value,
                    msg.ctx
                )

    def __topic_reader_worker(self):
        """
        Worker function for reading topics
        """

        handlers: List[Thread] = []
        while self.running:
            new_subscriber = self.pending_subscriptions.get()
            # Launch new thread

            handler = Thread(
                target=self.__topic_subscription_worker,
                args=[new_subscriber]
            )
            handlers.append(handler)
            handler.start()

        # Join all threads
        [h.join() for h in handlers]

        sys.stdout.flush()

    def __tick_handler(self):
        """
        Handler function for ticking the node
        """
        # Check tick rate from configuration
        if self.config is None:
            raise RuntimeError(f'''
    Configuration was not found when initializing tick handler for node
    {self}, with inner node: {self.inner_node.filename}
            ''')

        dt = 1.0 / self.config.tick_rate
        last_tick = time.time()

        while self.running:
            current_time = time.time()
            elapsed_time = current_time - last_tick

            if elapsed_time >= dt:
                self.inner_node.tick(self)
                sys.stdout.flush()
                last_tick = current_time
            else:
                time.sleep(dt - elapsed_time)
