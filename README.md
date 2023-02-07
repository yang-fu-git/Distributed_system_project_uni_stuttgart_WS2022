# Distributed Chat System

## Members of Group 2

This is an distributed Chat System realized by Python, it will use Server-Client Model and will fullfil the requirments of 
- Architecture model
- Dynamic discovery
- Fault tolerance
- Voting
- Ordered reliable multicast

## Usage
<ol start="1">
  <li>Open one terminal run the following to give permission <br>
    <code>chmod +x ./run_servers.sh</code> <br>
    <code>chmod +x ./stop_all.sh</code><br></li>
  <li>Run <br>
    <code> ./run_servers.sh  number</code> <br>
    to start number of servers <br>
    </li>
    <li>Open new terminal and run <br>
        <code>python client.py</code>
    </li>
    <li>write the message you wanna send in the running client terminal
    </li>
    <li>Repeat step 3 and 4 to add clients</li>
    <li>Open a new terminal and run <code>ps -T | grep server </code> to check all the running servers.<br> Run <code> kill PID</code> to kill servers </li>
    <li> Run <code>./stop_all</code> to kill all the threads</li>
</ol>




