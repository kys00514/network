from socket import *
from threading import Thread
import random
import time

serverIP = '127.0.0.1' # special IP for local host
serverPort = 12000
clientPort = 12001
tot=0
win = 1      # window size
no_pkt = 1000 # the total number of packets to send
send_base = 0 # oldest packet sent
loss_rate = 0.05 # loss rate
seq = 0        # initial sequence number
timeout_flag = 0 # timeout trigger
ssthresh=999
prevloss=-1
sent_time = [0 for i in range(2000)] # initialize sent_time array for recording sent time of packets


clientSocket = socket(AF_INET, SOCK_DGRAM) # create socket
clientSocket.bind(('', clientPort)) #bind port of socket
clientSocket.setblocking(0) #turns off blocking of the clientsocking, making it ready to receiving packets

# thread for receiving and handling acks
def handling_ack():
    global win # gloabal variable win to manage the window size of TCP connection
   
    global ssthresh
    print("                             window:"+str(win)+" "+str(ssthresh)) 
    global clientSocket
    global send_base
    global timeout_flag
    global sent_time
   
    alpha = 0.125
    beta = 0.25
    timeout_interval = 10  # timeout interval
    lost=[]
    
    pkt_delay = 0
    dev_rtt = 0
    init_rtt_flag = 1
    prev=-1
    count=0
    while True: #while loop for handling acks
        
        if sent_time[send_base] != 0:  #if the send_base packet was sent by packet sending thread
            pkt_delay = time.time() - sent_time[send_base]       #get packet delay be subtracting current time from sent time
        if pkt_delay > timeout_interval and timeout_flag == 0:    # timeout detected
            print("timeout detected:", str(send_base), flush=True)
            print("timeout interval:", str(timeout_interval), flush=True)
            dis=send_base in lost
            if(dis == False):
                
                timeout_flag=1 #set timeout flag so that retransmission can occur
            lost.append(send_base)
           # print("                     win size and ssthresh"+ str(win)+" "+str(ssthresh))
            
        try: #try except block for receiving acks
            ack, serverAddress = clientSocket.recvfrom(2048) # read from port used by server to send acks
            
            ack_n = int(ack.decode()) #decode the message to get the cumulative ack
            if(ack_n==send_base): # if received ack sequence number is equal to send base, it means window size can be increased 
                if(win*2<ssthresh):
                    win=win*2
                else:
                    win=win+1 #window size is increased by 1 when anticipated ack message is received
                print("                     win size and ssthresh"+ str(win)+" "+str(ssthresh))
            if(prev==ack_n): #if received ack is same as the previous ack, count is increased by one
                count=count+1
            
                
            if(prev!=ack_n): #if received ack is not same as the previous ack, count is initialized to 0
                count=0
            prev=ack_n # prev is updated to ack, if it is the same it will not be updated and the count will be increased in next iteration

           #print("got ack"+str(ack_n), flush=True)
            
            if init_rtt_flag == 1: #if no previous packets, estimated rtt is the first packet delay, then the init_rtt flag is set to 0
                estimated_rtt = pkt_delay
                init_rtt_flag = 0
            else: #if the init_rtt flag is not set, the estimated rtt, dev_rtt and timeout interval are calculated through the formulas
                estimated_rtt = (1-alpha)*estimated_rtt + alpha*pkt_delay
                dev_rtt = (1-beta)*dev_rtt + beta*abs(pkt_delay-estimated_rtt)
            timeout_interval = estimated_rtt + 4*dev_rtt
         
            #print("timeout interval:", str(timeout_interval), flush=True)
            if(count==3): # if 3 duplicate acks received retransmit and set ssthresh to half of window, then set window to 1
                print("triple duplicate retransmission"+str(ack_n+1),flush=True) 
                dis2=(ack_n+1) in lost
                if(dis2 == False):
                    timeout_flag=1  # resend seq to server in case of triple duplicate ack
                lost.append(ack_n+1)
             
            
        except BlockingIOError:
            continue
            
        # window is moved upon receiving a new ack
        # window stays for cumulative ack
        send_base = ack_n + 1 #send base is set to ack_n +1 due to cumulative ack, the packets before ack_n are all finished
        
        if ack_n == 999: # when 1000th ack arrives, break while loop
            print("all done")
            break # break while loop

# running a thread for receiving and handling acks
th_handling_ack = Thread(target = handling_ack, args = ()) # create thread for handling acks
th_handling_ack.start() # start thread
realstart=time.time() # measure time for throughput, latency calculation

while (True): # while loop in main thread to send packets to server

    while( seq < send_base + win and seq<1000): # send packets within window
      if random.random() < 1 - loss_rate: # send packets randomly with at percentage of loss rate
        clientSocket.sendto(str(seq).encode(), (serverIP, serverPort))  # send packet
       
      else:
        print("Packet Loss Simulated" + str(seq),flush=True)
      sent_time[seq] = time.time()    # save the time of departure of seq in the sent_time array
      seq = seq + 1 # 1 is added to seq so that all packets in windows are sent to server
      tot=tot+1
    
        
    if timeout_flag == 1: # when retransmission flag is 1, retransmission to server
        seq = send_base # seq number needs to be adjusted to send base
        clientSocket.sendto(str(seq).encode(), (serverIP, serverPort)) #retransmission of seq packet
        sent_time[seq] = time.time() #sent time 
        print("retransmission:", str(seq), flush=True)
        seq = seq + 1 # 1 is added to seq number
        timeout_flag = 0 #timeout flag is set to 0 again
        ssthresh=win//2
        win=1
    if (send_base==1000 and timeout_flag==0): # if get cumulative ack for 1000th packet, break the while loop
        break
print("out of loop")   
realend=time.time()   #time of the entire process of sending and receiving ack of 1000 packets
th_handling_ack.join() # terminating thread

print (realend-realstart) #print total time
print(tot)
input()
clientSocket.close() #close socket

