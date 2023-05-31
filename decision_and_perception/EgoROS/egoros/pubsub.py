import multiprocessing
from typing import Any, Callable, List, Optional
import logging
from dataclasses import dataclass, field
from datetime import datetime
import inspect

log = logging.getLogger('egoros')


@dataclass
class MessageContext:
    """
    Represents the context of a message with a timestamp.
    """

    timestamp: datetime


@dataclass
class Message:
    """
    Represents a message with its value and context.
    """

    value: Any
    ctx: MessageContext


@dataclass
class Subscription:
    """
    Represents a subscription with a message queue and callbacks.
    """

    msg_queue: multiprocessing.Queue = multiprocessing.Queue()
    callbacks: List[Callable[[Any, MessageContext], None]] = field(default_factory=lambda: [])


class Topic:
    """
    Represents a topic for publishing and subscribing to messages.
    """

    def __init__(self, name: str) -> None:
        """
        Constructor for the Topic class.
        @param name: The name of the topic.
        """
        self.type: Optional[type] = None
        self.name = name
        self.subscribers: List[Callable[[Any, MessageContext], None]] = []

    def publish(self, data: Any):
        """
        Publishes data to the topic, triggering the callbacks of all subscribers.
        @param data: The data to be published.
        """
        if self.type == None:
            self.__set_type(type(data))

        # Check if types are valid
        if self.type != None and self.type == type(data):
            # Create new MessageContext
            ctx = MessageContext(
                timestamp=datetime.now()
            )
            # Run all callbacks
            for sub in self.subscribers:
                sub(data, ctx)
        elif self.type != None:
            # Invalid data was passed
            msg = f'''
    Tried to publish "{data}" of type "{type(data)}".
    The type of the topic "{self.name}" has already been established to be "{self.type}"
            '''
            log.error(msg)
            raise TypeError(msg)

    def subscribe(self, callback: Callable[[Any, MessageContext], None]):
        """
        Subscribes to the topic with a callback function.
        @param callback: The callback function to be triggered when a message is received.
        """
        # Get information about callback
        callback_spec = inspect.getfullargspec(callback)

        if not len(callback_spec.args) == 2:
            msg = f'''
    Provided callback has an insufficient number of arguments ({len(callback_spec.args)})
            '''
            log.error(msg)
            raise TypeError(msg)

        fst_type: Optional[type] = callback_spec.annotations[
            callback_spec.args[0]] if callback_spec.args[0] in callback_spec.annotations else None
        snd_type: Optional[type] = callback_spec.annotations[
            callback_spec.args[1]] if callback_spec.args[1] in callback_spec.annotations else None

        # Check if found types are valid
        if snd_type != None and snd_type != MessageContext:
            msg = f'''
    Argument of type "{snd_type}" provided as a second argument for callback.
    The callback of a subscription should always be "MessageContext"
            '''
            log.error(msg)
            raise TypeError(msg)

        if fst_type != None:
            if self.type == None:
                self.__set_type(fst_type)
            elif self.type != fst_type:
                msg = f'''
    Tried to subscribe to the topic "{self.name}" of type "{self.type}" with an invalid callback.
    The callback's first argument should be of type "{self.type}" but it's of type "{fst_type}"
                '''
                log.error(msg)
                raise TypeError(msg)

        # Add callback to list
        self.subscribers.append(callback)

    def __set_type(self, t: type):
        """
        Sets the type of the topic.
        @param t: The type to set.
        """
        self.type = t
        log.info(f'''Set type for topic "{self.name}" to "{self.type}"''')
        print(f'Setting type of topic {self.name} to be {self.type}')


if __name__ == "__main__":
    topic = Topic('lidar')

    def foo(msg: int, ctx: MessageContext):
        """
        Example callback function for subscribing to the topic.
        @param msg: The message value.
        @param ctx: The message context.
        """
        print(msg, ctx)

    topic.publish("Texto")
    topic.subscribe(foo)
