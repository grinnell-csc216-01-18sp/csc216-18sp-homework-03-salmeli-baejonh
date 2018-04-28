##
# CSC 216 (Spring 2018)
# Reliable Transport Protocols (Homework 3)
#
# Sender-receiver code for the RDP simulation program.  You should provide
# your implementation for the homework in this file.
#
# Your various Sender implementations should inherit from the BaseSender
# class which exposes the following important methods you should use in your
# implementations:
#
# - sender.send_to_network(seg): sends the given segment to network to be
#   delivered to the appropriate recipient.
# - sender.start_timer(interval): starts a timer that will fire once interval
#   steps have passed in the simulation.  When the timer expires, the sender's
#   on_interrupt() method is called (which should be overridden in subclasses
#   if timer functionality is desired)
#
# Your various Receiver implementations should also inherit from the
# BaseReceiver class which exposes thef ollowing important methouds you should
# use in your implementations:
#
# - sender.send_to_network(seg): sends the given segment to network to be
#   delivered to the appropriate recipient.
# - sender.send_to_app(msg): sends the given message to receiver's application
#   layer (such a message has successfully traveled from sender to receiver)
#
# Subclasses of both BaseSender and BaseReceiver must implement various methods.
# See the NaiveSender and NaiveReceiver implementations below for more details.
##

from sendrecvbase import BaseSender, BaseReceiver

import Queue

class Segment:
    def __init__(self, msg, dst, bit=None, acknum=None):
        self.msg = msg
        self.dst = dst
        self.bit = bit
        self.acknum = acknum

class NaiveSender(BaseSender):
    def __init__(self, app_interval):
        super(NaiveSender, self).__init__(app_interval)

    def receive_from_app(self, msg):
        seg = Segment(msg, 'receiver')
        self.send_to_network(seg)

    def receive_from_network(self, seg):
        pass    # Nothing to do!

    def on_interrupt(self):
        pass    # Nothing to do!

class NaiveReceiver(BaseReceiver):
    def __init__(self):
        super(NaiveReceiver, self).__init__()

    def receive_from_client(self, seg):
        self.send_to_app(seg.msg)

class AltSender(BaseSender):
  def __init__(self, app_interval):
        super(AltSender, self).__init__(app_interval)
        self.bit = True
        self.old_seg = None
  
  def receive_from_app(self, msg):
    self.disallow_app_msgs()
    seg = Segment(msg, 'receiver', self.bit)
    old_seg = Segment(msg, 'receiver', self.bit)
    self.send_to_network(seg)
    self.old_seg = old_seg
    self.start_timer(self.app_interval)

  def receive_from_network(self, seg):
    if (seg.bit == self.bit and seg.msg == "ACK"): 
      self.end_timer()
      self.bit = not self.bit
      self.allow_app_msgs()

  def on_interrupt(self):
    seg = Segment(self.old_seg.msg, 'receiver', self.old_seg.bit)
    self.send_to_network(seg)
    self.start_timer(self.app_interval)
    pass

  def s_handshake(self, seg=None):
    if seg == None:
      SYN = Segment("SYN", 'receiver')
      self.send_to_network(SYN)
    elif seg.msg == 'SYN-ACK':
      ACK = Segment("ACK", 'receiver')
      self.send_to_network(ACK)

  def s_close(self, seg=None):
    flag = False
    if seg == None:
      FIN = Segment("FIN", 'receiver')
      self.send_to_network(FIN)
    elif seg.msg == 'FIN':
      ACK = Segment("ACK", 'receiver')
      self.send_to_network(ACK)
    elif seg.msg == 'ACK':
      flag = True
    return flag

class AltReceiver(BaseReceiver):
  def __init__(self):
        super(AltReceiver, self).__init__()
        self.bit = True
        self.connected = False

  def r_handshake(self, seg):
    flag = False
    if seg.msg == 'SYN':
      SYNACK = Segment('SYN-ACK', 'sender')
      self.send_to_network(SYNACK)
    elif seg.msg == 'ACK':
       self.connected = True
       flag = True
    return flag

  def r_close(self, seg=None):
    flag = False
    if seg == None:
      FIN = Segment("FIN", 'sender')
      self.send_to_network(FIN)
    elif seg.msg == 'FIN':
      ACK = Segment("ACK", 'sender')
      self.send_to_network(ACK)
    elif seg.msg == 'ACK':
      flag = True
    return flag

  def receive_from_client(self, seg):
    if(seg.msg == '<CORRUPTED>'):
      NAK = Segment("ACK", 'sender', not self.bit)
      self.send_to_network(NAK)
    elif (self.bit != seg.bit):
      bad = Segment("ACK", 'sender', not self.bit)
      self.send_to_network(bad)
    else:
      self.send_to_app(seg.msg)
      ACK = Segment("ACK", 'sender', self.bit)
      self.send_to_network(ACK)
      self.bit = not self.bit

class GBNSender(BaseSender):
  def __init__(self, app_interval):
        super(GBNSender, self).__init__(app_interval)
        self.base = 1
        self.nextseqnum = 1
        self.N = 4

  def receive_from_app(self, msg):
    if(self.nextseqnum<self.base+self.N):
      seg = Segment(msg, 'receiver', self.nextseqnum)
      self.send_to_network(seg)
      if(self.base==self.nextseqnum):
        self.start_timer(self.app_interval)
      self.nextseqnum += 1

  def receive_from_network(self, seg):
    if(seg.msg == '<CORRUPTED>'):
      pass
    else:
      self.base = seg.bit + 1
      if(self.base==self.nextseqnum):
        self.end_timer()
      else:
        self.start_timer(self.app_interval)

  def on_interrupt(self):
    self.start_timer(self.app_interval)
    self.nextseqnum = self.base

  def s_handshake(self, seg=None):
    flag = False
    if seg == None:
      SYN = Segment("SYN", 'receiver', bit=0, acknum=0)
      self.send_to_network(SYN)
      flag = True
    elif seg.msg == 'SYN-ACK':
      ACK = Segment("ACK", 'receiver', bit=0, acknum=1)
      self.send_to_network(ACK)
      flag = True
    return flag

  def s_close(self, seg=None):
    flag = False
    if seg == None:
      FIN = Segment("FIN", 'receiver')
      self.send_to_network(FIN)
    elif seg.msg == 'FIN':
      ACK = Segment("ACK", 'receiver')
      self.send_to_network(ACK)
    elif seg.msg == 'ACK':
      flag = True
    return flag

class GBNReceiver(BaseReceiver):
  def __init__(self):
        super(GBNReceiver, self).__init__()
        self.expectedseqnum = 1

  def receive_from_client(self, seg):
    if(seg.msg == '<CORRUPTED>'):
      pass
    else:
      self.send_to_app(seg.msg)
      ACK = Segment('ACK', 'sender', self.expectedseqnum)
      self.send_to_network(ACK)
      self.expectedseqnum += 1

  def r_handshake(self, seg):
    flag = False
    if seg.msg == 'SYN':
      SYNACK = Segment('SYN-ACK', 'sender', bit=0, acknum=1)
      self.send_to_network(SYNACK)
    elif seg.msg == 'ACK':
       self.connected = True
       flag = True
    return flag

  def r_close(self, seg=None):
    flag = False
    if seg == None:
      FIN = Segment("FIN", 'sender')
      self.send_to_network(FIN)
    elif seg.msg == 'FIN':
      ACK = Segment("ACK", 'sender')
      self.send_to_network(ACK)
    elif seg.msg == 'ACK':
      flag = True
    return flag
