#Inital Plans
MD file for what my inital plans are for the website

##Main Idea
A web application similar to draw.io except instead of creating the nodes and connections yourself, they are populated for you based on form input. There should be two main pages, the investigation page where you can view the created graph and the documents page where you create the document nodes. There should be four starting types of nodes. Each node will have a list of information contained within it that will then populate object types for each node type. To create relationships between nodes, the program must connect them through the db. An example of this is included below. Once a graph is completed a user must be able to download the graph as a png image. If an agent chooses to save the investigation for later, they can choose to export the information to an organized csv file. Likewise, the program must be able to load a csv file of information.

For color scheme on the web application, I want to use the following colors, matching a crimson voltage pallete I found online:
131313
394249
D2CDCB
D26D6F
C11E20

##Detailed feature information
###Investigation Page
This is the main page of the application. Opening the web app brings you right here. There should be a popup for "load investigation" or "start new investigation". The page will be a blank white canvas. As a user fills out forms in the document section, cytoscape will be used to graph out the nodes and relationships on the Invesigation page. cytoscape should pull its information from created node objects. If no node objects exist, ie in a new project, then the page should stay blank with greyed text in the middle saying "add forms to begin graphing"

###Documents Page
This page is where users can fill out and manage the investigation reports they have contained in the application. The following sections dictate the information for Transactions, Gift Cards, Online Orders, and Misc Nodes. Information that is required will be marked with a *. All information fields are followed by their expected format. For the main section of this page, all documents should be listed in a list order. This list should have the option to filter by document type and have alphabetical sorting. All nodes should have an option to add notes.

####Transaction Node
Transaction number*: XXXXXXXX INT
date*: MM-DD-YYYY
time*: 2400
register number: XXX INT
store number: XXX INT
payment type*: Dropdown listing Credit Card, Gift Card, Cash, Other. The program should allow multiple payments to be added to a single transaction. If the option selected is Gift Card, then the user should have a text box for giving the gift card number. After selecting the option from the dropdown, have a second field to state how much from each payment method in the format of $XXX.XX. The end format should look like:
	[Payment Type] $XXX.XX REAL
	[Payment Type] $XXX.XX REAL

####Gift Card Node
Gift Card number*: XXXXXXXXXXXXXXXXXXXXXXXX INT

#####Activation information
activation transaction number*: XXXXXXXX INT
activation date*: DD-YYYY
activation time*: 2400
activation store number: XXX INT
activation amount: $XXXX.XX REAL

#####History information
You should be able to add a list of connected transactions. The following information would be needed for each transaction:

transaction number*: XXXXXXXX INT
date*: DD-YYYY
time*: 2400
store number: XXX INT
amount: $XXXX.XX REAL

####Online Order Node
Online Order number*: XXXXXXXX INT
placed date*: MM-DD-YYYY
placed time*: 2400
customer state: TEXT
customer city: XX TEXT
store number for pickup: XXX INT
payment type*: Dropdown listing Credit Card, Gift Card, Cash, Other. The program should allow multiple payments to be added to a single transaction. If the option selected is Gift Card, then the user should have a text box for giving the gift card number. After selecting the option from the dropdown, have a second field to state how much from each payment method in the format of $XXX.XX. The end format should look like:
	[Payment Type] $XXX.XX REAL
	[Payment Type] $XXX.XX REAL

####Misc Node
Node Name*: TEXT
date*: MM-DD-YYYY
time*: 2400
Transaction number: XXXXXXXX INT
Online Order number: XXXXXXXX INT
payments: Dropdown listing Credit Card, Gift Card, Cash, Other. The program should allow multiple payments to be added to a single transaction. If the option selected is Gift Card, then the user should have a text box for giving the gift card number. After selecting the option from the dropdown, have a second field to state how much from each payment method in the format of $XXX.XX. The end format should look like:
	[Payment Type] $XXX.XX REAL
	[Payment Type] $XXX.XX REAL

###How Relationship Are Made
The relationships made in cytoscape should be done entirely in the backend of the web application. The web application should go through the node objects created and potentially an SQLite organization of the data to determine which nodes are connected to each other. For example, a Gift Card node should contain information for its activation transaction. The information saved within this activation transaction should link the gift card to the transaction it is referencing. If a referenced gift card finds the transaction and vice versa, then all information is there for a complete connection.

Due to this system, there can be incomplete connections where a node references another node that doesnt exsist yet. if a node references another that does not exist, it should create an incomplete node and form within the documents page. The document should be highlighted to the user in the documents page and should be at 75% opacity on the investigation page. The big idea is incomplete or missing information should not throw an error but should instead be shown on the graph. 

###Exporting the graph
Exporting a graph should create a .png file of the graph. Graphs exported should be scaled and positioned so that all nodes fit within, and fill, either a landscape or portrait layout depending on user request.

###Saving/loading csv files
All data saved within the investigation should be able to be saved. There should be a save button in the top navigation bar that allows a user to save the investigation to a location on their desktop. The save button should generate a csv file with all needed information organized so that the csv itself is readable. Ideally, I imagine this to be a new sheet for each node type. There should also be a some form of information saved to indicate that this is a valid save file for the program.
For loading data, the program should accept csv files and read for the previously mentioned validity check created in a saved file. If data is loaded and errors occur, the user should be informed that the information is corrupted or incorrect, asking if they would like to proceed. If they choose to proceed, then load the data as best as possible.
Data should ideally be saved occasionally in the event of a website crash. 

###Security Concerns
During my requirements discovery, I had my two interviewees being up logins and accounts. I would like to implement google's IAM stack if it costs nothing. If there is an associated cost, then I would like to consider other avenues of IAM.
