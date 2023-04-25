from dataclasses import dataclass, field
import datetime
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

@dataclass
class MessageContext:
    """
    Context added to every message sent
    @param timestamp Timestamp when the message was sent
    """
    timestamp: datetime.datetime

@dataclass
class Message:
    """
    Topic message
    @param value Value published
    @param context Context of the published message
    """
    value: Any
    context: MessageContext

@dataclass
class Topic:
    """
    Topic
    @param name Name of the topic
    @param type Type of the topic's messages 
    @param subscribers Callbacks registered for the specified topic
    @param message_queue Stored messages for when the hub is paused
    """
    name: str
    type: Optional[Type]
    subscribers: List[Callable[[Any, MessageContext], None]] = field(default_factory=lambda: [])
    message_queue: List[Message] = field(default_factory=lambda: [])

class MessageHub:
    """
    Message hub that manages all topics subscriptions and publishers
    """
    def __init__(self) -> None:
        """
        Constructor
        """
        self.topics: Dict[str, Topic] = {}
        self.halted = False

    def pause(self):
        """
        Pauses the message forwarding (useful when loading all nodes)
        @details
        All of the messages that are published while the hub is paused will be stored inside a queue
        """
        self.halted = True

    def resume(self):
        """
        Resumes the message forwarding and sends all the stored messages
        """
        self.halted = False
        for topic in self.topics.values():
            for msg in topic.message_queue:
                for sub in topic.subscribers:
                    sub(msg.value, msg.context)
            topic.message_queue = [] # Clear pending messages
                

    def publish(self, topic: str, arg: Any):
        """
        Publishes a message
        @param topic Topic to publish the data to
        @param arg Message to send to the topic
        """
        # Check if the topic already exists to create it if neccessary
        generated_context = MessageContext(
            timestamp=datetime.datetime.now()
        )

        if not topic in self.topics:
            self.topics[topic] = Topic(
                name=topic,
                type=type(arg),
            )
            if self.halted: # Only action taken is if the hub is paused
                self.topics[topic].message_queue.append(Message(
                    value=arg,
                    context=generated_context
                ))
        else: # Topic already exists
            # Check if argument is of the neccessary type
            type_id = type(arg)
            if self.topics[topic].type == None:
                self.topics[topic].type = type_id
            elif not self.topics[topic].type == type_id:
                print(f'''
    Failed to publish to an already created topic "{topic}" of type {self.topics[topic].type}.
    Tryping to publish value "{arg}" of type {type_id}
                ''')

            if self.halted: # If it's halted, add it to the message queue
                self.topics[topic].message_queue.append(Message(
                    value=arg,
                    context=generated_context
                ))
            else: 
                for sub in self.topics[topic].subscribers:
                    sub(arg, generated_context)

    def subscribe(self, topic: str, callback: Callable[[Any, MessageContext], None]):
        """
        Adds a callback to the specified topic
        @param topic Topic to subscribe to
        @param callback Method to run when a message is published in the topic
        """
        # Check if action already exists
        callback_spec = inspect.getfullargspec(callback)
        type_id = None 
        if callback_spec.args[0] in callback_spec.annotations:
            type_id = callback_spec.annotations[callback_spec.args[0]]

        print(f'Detected type: {type_id}')

        if not topic in self.topics:
            self.topics[topic] = Topic(
                name=topic,
                type=type_id,
            )
            print(f'Creating new topic {topic} of type {type_id}')
            self.topics[topic].subscribers.append(callback)
        else:
            # Check if type was not specified yet
            if self.topics[topic].type == None:
                self.topics[topic].type = type_id

            if type_id != self.topics[topic].type and not type_id == None:
                raise TypeError(f'''
    Trying to subscribe to the existing topic "{topic}" with a method that takes a {type_id}.
    You have to subscribe to a topic with the same type it was created ({self.topics[topic].type})
                ''')

            # Add the callback
            self.topics[topic].subscribers.append(callback)


if __name__ == "__main__":
    hub = MessageHub()
    def callback(arg):
        print(arg)

    def foo(arg: int, context: MessageContext):
        print(f'Callback: {arg}')
        print(f'ctx: {context}')

    def fuu(arg: float):
        print(f'Float: {arg}')

    hub.subscribe('lidar', foo)
    hub.publish('lidar', 123)


