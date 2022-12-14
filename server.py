from socket import *
from threading import Thread
from queue import Queue
import time # 1~4 import needed libraries


serverPort = 12000 # determine server port#

serverSocket = socket(AF_INET, SOCK_DGRAM) #create socket
serverSocket.bind(('', serverPort)) #bind socket

print('The server is ready to receive')

rcv_base = 0  # next sequence number we wait for
def receivepackets(connectqueue): #method for receiving packets and sending them through
    start=time.time() # start timer
    while(True): # while loop for receiving packets from client
        message, clientAddress = serverSocket.recvfrom(2048) # receive packet
        seq_n = int(message.decode()) # extract sequence number
        print("received:"+str(seq_n)) #print received seq_n
        if(seq_n==0):
            connectqueue.put(clientAddress) #if first received packet, send client address thru queue as well for thread that sends ack
        if(connectqueue.qsize()<21): #20 is the queue size, if full, drop packets (packet loss simulation)
            connectqueue.put(seq_n) #if queue is not full, put seq_n in queue for ack sending thread to receive


q = Queue() # create queue
th_receivepackets=  Thread(target =receivepackets, args =(q, )) # create thread for receiving packets, gives queue as parameter 
th_receivepackets.start() #start queue
realclientAddress=-1 #initialize client address
rcv_base = 0 #initialize rcv_base (used for cumulative ack)
while True: # while loop for reading from queue and sending acks

    recvmessage=q.get() # get seq_n of received packets from queue
    if(realclientAddress==-1): #if client address is not received from queue yet 
        realclientAddress=recvmessage # read from queue and set the client address as the receieved message from queue (the first packet sent from queue is the client address)
        continue
    if recvmessage == rcv_base: # in order delivery
        rcv_base = recvmessage + 1 # rcv_base is incresed by one if expec
    serverSocket.sendto(str(rcv_base-1).encode(), realclientAddress) # send cumulative ack
    print("sent "+str(rcv_base-1))
    time.sleep(0.15) #sleep in order to mimic queue processing delay
    if rcv_base == 1000: #if all packets received stop
        print("we will stop")
        break
    

input()
serverSocket.close()


