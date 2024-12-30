# Final Skeleton
#
# Hints/Reminders from Lab 3:
#
# To check the source and destination of an IP packet, you can use
# the header information... For example:
#
# ip_header = packet.find('ipv4')
#
# if ip_header.srcip == "1.1.1.1":
#   print "Packet is from 1.1.1.1"
#
# Important Note: the "is" comparison DOES NOT work for IP address
# comparisons in this way. You must use ==.
#
# To send an OpenFlow Message telling a switch to send packets out a
# port, do the following, replacing <PORT> with the port number the
# switch should send the packets out:
#
#    msg = of.ofp_flow_mod()
#    msg.match = of.ofp_match.from_packet(packet)
#    msg.idle_timeout = 30
#    msg.hard_timeout = 30
#
#    msg.actions.append(of.ofp_action_output(port = <PORT>))
#    msg.data = packet_in
#    self.connection.send(msg)
#
# To drop packets, simply omit the action.
#
from pox.core import core
import pox.openflow.libopenflow_01 as of
log = core.getLogger()
class Final (object):
  """
  A Firewall object is created for each switch that connects.
  A Connection object for that switch is passed to the __init__ function.
  """
  def __init__ (self, connection):
    # Keep track of the connection to the switch so that we can
    # send it messages!
    self.connection = connection
    # This binds our PacketIn event listener
    connection.addListeners(self)
  def do_final (self, packet, packet_in, port_on_switch, switch_id):
    # This is where you'll put your code. The following modifications have
    # been made from Lab 3:
    # - port_on_switch: represents the port that the packet was received on.
    # - switch_id represents the id of the switch that received the packet.
    #   (for example, s1 would have switch_id == 1, s2 would have switch_id == 2, etc...)
    # You should use these to determine where a packet came from. To figure out where a packet
    # is going, you can use the IP header information.
    ip_header = packet.find('ipv4')
    if packet.find('arp'):
      message = of.ofp_packet_out()
      message.data = packet_in
      message.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
      self.connection.send(message)
      return
    if ip_header:
      source_ip = str(ip_header.srcip)
      destination_ip = str(ip_header.dstip)
      # block all IP traffic from untrusted hosts to server
      # block all ICMP traffic from untrusted hosts to anywhere internally
      if source_ip == '108.35.24.113':
        if destination_ip.startswith('128.114.'):
          return
        if packet.find('icmp'):
          return
      # block ICMP and IP traffic from trusted hosts to server
      # block ICMP traffic from trusted hosts to department B
      if source_ip == '192.47.38.109':
        if destination_ip.startswith('128.114.3.') or destination_ip.startswith('128.114.2.'):
          return
        if packet.find('icmp') and destination_ip.startswith('128.114.2.'):
          return
      # block all ICMP traffic from hosts in department A to department B and vise versa
      if source_ip.startswith('128.114.1.') and packet.find('icmp') and destination_ip.startswith('128.114.2.'):
        return
      if source_ip.startswith('128.114.2.') and packet.find('icmp') and destination_ip.startswith('128.114.1.'):
        return
      # everything else is allowed
      message = of.ofp_flow_mod()
      message.match = of.ofp_match.from_packet(packet)
      message.idle_timeout = 30
      message.hard_timeout = 30
      message.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      message.data = packet_in
      self.connection.send(message)
  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch.
    """
    packet = event.parsed # This is the parsed packet data.
    if not packet.parsed:
      log.warning("Ignoring incomplete packet")
      return
    packet_in = event.ofp # The actual ofp_packet_in message.
    self.do_final(packet, packet_in, event.port, event.dpid)
def launch ():

    '''
    Starts the component
    '''
    def start_switch (event):
        log.debug("Controlling %s" % (event.connection,))
        Final(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)