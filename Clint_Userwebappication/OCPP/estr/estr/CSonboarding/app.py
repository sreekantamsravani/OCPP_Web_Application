from flask import * 
import mysql.connector
import uuid
import time
import datetime

import requests



#Flask, render_template, request, redirect, url_for

# MySQL configurations
connection = mysql.connector.connect(host="localhost", port= 3306, user="root", passwd="12345", database="ocpp")
cursor = connection.cursor()

app = Flask(__name__)    #This creates a new Flask application instance, named app.

app.secret_key = "supersecretkey" #This sets the secret key for the Flask application. The secret key is used to encrypt session data, and should be kept secret and secure.


@app.route('/')
def test():
    session.clear()
    session_id = request.cookies.get('session_id')
    print(session_id)
    cursor.execute("SELECT Session_Id FROM cs_registration WHERE Session_Id=%s", (session_id,))
    SESSION_ID = cursor.fetchone()
    print(SESSION_ID)
    if SESSION_ID is None:
        return redirect(url_for('login_redirect'))
    else:
        
        return redirect(url_for('home', session_id=session_id))


@app.route('/login_redirect', methods=('POST','GET'))
def login_redirect():
    if request.method == 'POST':
        user_type = request.form['userType']
        if user_type == 'chargingStation':
            
            return redirect(url_for('login'))
        elif user_type == 'endUser':
            return redirect(url_for('UserLogin'))
        
    return render_template('login_redirect.html')



@app.route('/home', methods=('GET', 'POST'))
def home():
       
    SESSION_ID = request.cookies.get('session_id')
    if SESSION_ID is not None:
        cursor.execute("SELECT * FROM cs_registration WHERE Session_Id=%s",(SESSION_ID,))
        personal_Data1 = cursor.fetchone()
        session['sessionID']={'session_id':SESSION_ID}

        
        print(type(personal_Data1[0][1])) 
        return render_template('home.html', personal_Information=personal_Data1, session_id=SESSION_ID)
       #return "Nothing"
    else:
        return "Something Wrong"






@app.route('/login', methods=('GET', 'POST'))
def login():
    
    if request.method == 'POST':
        
          # Get form data
        Email = request.form['email']
        Password = request.form['password']
        session['Login_credentials'] = {'Email': Email, 'Password': Password}
        
        print(Email)
        cursor.execute("SELECT * FROM cs_registration WHERE Email=%s", (Email,))
        user = cursor.fetchone()
        print(user)
        print("get user and email")
         
        if user is None:
        
            message="Please provide valid Email and password"
            return render_template('Userlogin.html', message=message)
           
        elif user[1] == Password:        
            session_id=str(uuid.uuid4())
            session['Email'] = Email
            session['session_id'] = session_id
            
            cursor.execute("UPDATE cs_registration SET Session_Id=%s WHERE Email=%s", (session['session_id'],Email,))
            connection.commit()
            
            resp = make_response(redirect(url_for('home',session_id=session['session_id'])))
            expires_date = datetime.datetime.now() + datetime.timedelta(days=7)  
            resp.set_cookie('session_id', session_id, expires=expires_date)
            return resp       
        else:
            message="The password does not match"
         
            return render_template('login.html', message=message)

    return render_template('login.html')  

 

@app.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
          # Get form data
        Name = request.form['name']
        Email    = request.form['email']
        Registered_Mobile_Number = request.form['phoneNumber']
        Address = request.form['address']
        City = request.form['city']
        State=request.form['state']
        Pincode=request.form['pincode']


        session['personal_details'] = {'Name': Name, 'Email': Email, 'Registered_Mobile_Number':Registered_Mobile_Number, 'Address':Address, 'City':City, 'State':State,  'Pincode':Pincode}
             
        return redirect(url_for('create_credentials'))
    else:
            
        return render_template('signup.html')
    
    




@app.route('/create_credentials', methods=('GET', 'POST'))
def create_credentials():
    if request.method == 'POST':
          # Get form data
        Username = request.form['username']
        Password = request.form['password']
        
        ##create session for credentials
        session['credentials_details'] = {'Username': Username, 'Password': Password}
        return redirect(url_for('station'))
    else:

        return render_template('create_credentials.html')







@app.route('/station', methods=('GET', 'POST'))
def station():
    SESSION_ID = request.cookies.get('session_id')
    

    
    if request.method == 'POST':
          # Get form data
        VendorName = request.form['vendorname']
        Model = request.form['model']
        Firmware = request.form['firmware']
        Serial_Number = request.form['serialname']
        Modem = request.form['modem']
        Location = request.form['location']
        No_of_EVSEs = request.form['numberOfEVSEs']
        No_of_Connectors_On_Each_EVSEs = request.form['numberOfConnectors']
        Cable_Capacity = request.form['cablecapacity']

        session['Num_EVSE_Connectors'] = {'No_of_EVSEs': No_of_EVSEs, 'No_of_Connectors_On_Each_EVSEs': No_of_Connectors_On_Each_EVSEs}
        
        
        #Get personal details from sign-up page using session get method
        personal_details = session.get('personal_details', None)

        #Get Credential Details from session[credentials_details]
        credentials_details = session.get('credentials_details', None)

        
        

        session['station_details']={'Vendor_Name':VendorName, 'Model':Model, 'Firmware':Firmware, 'Serial_Number':Serial_Number,'Modem':Modem, 'Location':Location, 'No_of_EVSEs':No_of_EVSEs, 'No_of_Connectors_On_Each_EVSEs':No_of_Connectors_On_Each_EVSEs, 'Cable_Capacity':Cable_Capacity}
        cursor.execute("SELECT Username  FROM cs_registration WHERE Session_Id=%s", (SESSION_ID,))
        UserName = cursor.fetchone()

        if personal_details and credentials_details is not None:
            cursor.execute("SELECT * FROM chargingstation WHERE vendorName=%s", (VendorName,))
            user = cursor.fetchone()


            session['Vendor_details']={'Vendor_Name':VendorName, 'Username': credentials_details['Username']}
            
            
            if user is None :
            # No matching row was found
                cursor.execute("INSERT INTO cs_registration (Name, Email, Registered_Mobile_Number, Address, City, State, Pincode, Username, Password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (personal_details['Name'], personal_details['Email'], personal_details['Registered_Mobile_Number'], personal_details['Address'], personal_details['City'], personal_details['State'], personal_details['Pincode'], credentials_details['Username'], credentials_details['Password']))
                connection.commit()
                personal_details = session.pop('personal_details', None)
                
                

                return redirect(url_for('payment'))
               # return redirect(url_for('cs_verification'))
           
            elif user[3]== VendorName:
            # The password matches, so redirect to the home page
            
                return render_template('login.html')
            else:

                return render_template('login.html')
        else:

            
            cursor.execute("SELECT *  FROM cs_registration WHERE Session_Id=%s", (SESSION_ID,))
            UserName = cursor.fetchone()
            print(UserName)
            session['Vendor_details']={'Vendor_Name':VendorName, 'Username': UserName}

            session['UserName'] = {'UserName': UserName[0]}
            print(UserName)
            print("New Station reg")
            print(UserName)

                                  
            return redirect(url_for('payment'))
                
    else:
        
        return render_template('station.html')



@app.route('/payment', methods=('GET', 'POST'))
def payment():
    OwnerDetails = session.get('Vendor_details', None)
    Vendor_Name=OwnerDetails['Vendor_Name']
    Username=OwnerDetails['Username']
    UserName_details = session.get('UserName', None)
     
   
    if request.method == 'POST':
          # Get form data
        BankName = request.form['bankName']
        print(type(BankName))
        AccountNumber = request.form['accountNumber']
        print(type(AccountNumber))
        IFSC = request.form['ifscCode']
        print(type(IFSC))
        BranchName=request.form['branchName']
        print(type(BranchName))

        
        if Username is None:

            cursor.execute("INSERT INTO payment_details (bankName, accountNumber, IFSC_Code, branchName, vendorName, userName) VALUES (%s, %s, %s, %s, %s, %s)", (BankName, AccountNumber, IFSC, BranchName,Vendor_Name,UserName_details['UserName']))
            connection.commit()
        else:

            cursor.execute("INSERT INTO payment_details (bankName, accountNumber, IFSC_Code, branchName, vendorName, userName) VALUES (%s, %s, %s, %s, %s, %s)", (BankName, AccountNumber, IFSC, BranchName,Vendor_Name,Username))
            connection.commit()

        
        ##create session for credentials
        return redirect(url_for('energy_rate_card_form'))
    else:

        return render_template('payment.html')



@app.route('/energy_rate_card_form', methods=('GET', 'POST'))
def energy_rate_card_form():
    OwnerDetails = session.get('Vendor_details', None)
    Energy_card_Vendor_Name=OwnerDetails['Vendor_Name']
    Energy_card_Username=OwnerDetails['Username']

    UserName_details = session.get('UserName', None)
    
    if request.method == 'POST':
          # Get form data
        ChargingRate = request.form['chargingRate']
        MinimumFee = request.form['minimumFree']
        TimeBaseFee = request.form['timeBaseFee']
        NetworkFee=request.form['networkFee']
        GST=request.form['gst']
        if Energy_card_Username is None:

            cursor.execute("INSERT INTO energy_rate_card_details (chargingRate, minimumFee, timeBaseFee, networkFee, GST, vendorName, userName) VALUES (%s, %s, %s, %s, %s, %s, %s)", (ChargingRate, MinimumFee, TimeBaseFee, NetworkFee, GST, Energy_card_Vendor_Name, UserName_details['Username'],))
            connection.commit()
        else:
            cursor.execute("INSERT INTO energy_rate_card_details (chargingRate, minimumFee, timeBaseFee, networkFee, GST, vendorName, userName) VALUES (%s, %s, %s, %s, %s, %s, %s)", (ChargingRate, MinimumFee, TimeBaseFee, NetworkFee, GST, Energy_card_Vendor_Name, Energy_card_Username,))
            connection.commit()
        ##create session for credentials
        return redirect(url_for('login_auth'))
    else:

        return render_template('energy_rate_card_form.html')





@app.route('/login_auth', methods=('GET', 'POST'))
def login_auth():
    if request.method == 'POST':
          # Get form data
        Email = request.form['loginemail']
        Password = request.form['loginpassword']
        
        session['credentials'] = {'Email': Email, 'Password': Password}
        return redirect(url_for('cs_verification'))
    return render_template('login_auth.html')





@app.route('/cs_verification', methods=('GET', 'POST'))
def cs_verification():
    OwnerDetails = session.get('Vendor_details', None)
    Vendor_Name=OwnerDetails['Vendor_Name']
        
    Num_EVSE_Connectors = session.get('Num_EVSE_Connectors', None)
    station_details = session.get('station_details', None)
    
    
    num_evses = int(Num_EVSE_Connectors['No_of_EVSEs'])
    num_connectors = int(Num_EVSE_Connectors['No_of_Connectors_On_Each_EVSEs'])
    print(num_evses)
    print(type(num_evses))
    print(type(num_connectors))


    
    if request.method == 'POST':
          # Get form data
        

        CS_Status = request.form['csStatus']
        Vendor_Id = request.form['vendorId']

        Email_Password = session.get('credentials', None)
        if Email_Password is not None:
            cursor.execute("SELECT Username FROM cs_registration WHERE Email=%s",(Email_Password['Email'],))
            Username=cursor.fetchone()

            cursor.execute("INSERT INTO chargingstation (CS_Status, vendorId, vendorName) VALUES (%s, %s, %s)", (CS_Status, Vendor_Id, "NULL"))
            connection.commit()

           
            cursor.execute("UPDATE chargingstation SET vendorName=%s, model=%s,firmwareVersion=%s, Serial_Number=%s, Modem=%s, Location=%s, No_of_EVSEs=%s, No_of_Connectors_On_Each_EVSEs=%s, Cable_Capacity=%s, userName=%s WHERE vendorId=%s", (station_details['Vendor_Name'], station_details['Model'],station_details['Firmware'], station_details['Serial_Number'], station_details['Modem'], station_details['Location'], station_details['No_of_EVSEs'], station_details['No_of_Connectors_On_Each_EVSEs'], station_details['Cable_Capacity'], Username[0], Vendor_Id))
            connection.commit()
        
            
            evse_AND_Connectors_ids = {}
            for i in range(1, num_evses+1):
                evse_AND_Connectors_ids[f'EVSEID{i}'] = request.form[f'EVSEID{i}']
                for j in range(1, num_connectors+1):
                    evse_AND_Connectors_ids[f'ConnectorID{i}{j}'] = request.form[f'connectorID{i}{j}']
                    evse_AND_Connectors_ids[f'Connector{i}{j}_Type']= request.form[f'connectorType{i}{j}']
                    print("evse_AND_Connectors_ids")
                    print(evse_AND_Connectors_ids)

            Price = request.form['price']
            print("Price")

            for i in range(1, num_evses+1):
                evse_values = [(evse_AND_Connectors_ids[f'EVSEID{i}'], Vendor_Id, Username[0],)]
                insert_statement = "INSERT INTO evse1 (evseId, vendorId, Username) VALUES (%s, %s, %s)"
                print(evse_values)
                for val in evse_values:
                    cursor.execute(insert_statement, val)
                    print(val)
                    connection.commit()
                    
            print(" evse_values Its worked")



            connector_values = []
            for i in range(1, num_evses+1):
                for j in range(1, num_connectors+1):
                    connector_values.append((evse_AND_Connectors_ids[f'ConnectorID{i}{j}'], CS_Status, evse_AND_Connectors_ids[f'EVSEID{i}'], Vendor_Id, evse_AND_Connectors_ids[f'Connector{i}{j}_Type'],Username[0],Vendor_Name,))

            insert_statement = "INSERT INTO connector1 (connectorId, connectorStatus, evseId, vendorId, connectorType, userName, vendorName) VALUES (%s, %s, %s, %s, %s,%s,%s)"
            print(connector_values)
            


            for val in connector_values:
                cursor.execute(insert_statement, val)
                print(val)

            connection.commit()
            
            print("connector_values Its worked")
        
            return redirect(url_for('login'))
        else:
            UserName_details = session.get('UserName', None)
            
            
            cursor.execute("SELECT userName FROM chargingstation WHERE vendorName=%s", (Vendor_Name,))
            userName = cursor.fetchone()
        
            

            print("Verification ------")
            print(Vendor_Name)

                        

            evse_AND_Connectors_ids = {}
            for i in range(1, num_evses+1):
                evse_AND_Connectors_ids[f'EVSEID{i}'] = request.form[f'EVSEID{i}']
                for j in range(1, num_connectors+1):
                    evse_AND_Connectors_ids[f'ConnectorID{i}{j}'] = request.form[f'connectorID{i}{j}']
                    evse_AND_Connectors_ids[f'Connector{i}{j}_Type']= request.form[f'connectorType{i}{j}']
                    print("evse_AND_Connectors_ids")
                    print(evse_AND_Connectors_ids)

            Price = request.form['price']
            print("Price")
             
            cursor.execute("INSERT INTO chargingstation (CS_Status, vendorId, vendorName) VALUES (%s, %s, %s)", (CS_Status, Vendor_Id, "NULL"))
            connection.commit()

           
            cursor.execute("UPDATE chargingstation SET vendorName=%s, model=%s, firmwareVersion=%s, Serial_Number=%s, Modem=%s, Location=%s, No_of_EVSEs=%s, No_of_Connectors_On_Each_EVSEs=%s, Cable_Capacity=%s, userName=%s  WHERE vendorId=%s", (station_details['Vendor_Name'], station_details['Model'], station_details['Firmware'], station_details['Serial_Number'], station_details['Modem'], station_details['Location'], station_details['No_of_EVSEs'], station_details['No_of_Connectors_On_Each_EVSEs'], station_details['Cable_Capacity'], UserName_details['UserName'], Vendor_Id))
            connection.commit()
            
            
            for i in range(1, num_evses+1):
                evse_values = [(evse_AND_Connectors_ids[f'EVSEID{i}'], Vendor_Id, UserName_details['UserName'],)]
                insert_statement = "INSERT INTO evse1 (evseId, vendorId, Username) VALUES (%s, %s, %s)"
                print(evse_values)
                for val in evse_values:
                    cursor.execute(insert_statement, val)
                    print(val)
                    connection.commit()
                    
            print(" evse_values Its worked")



            connector_values = []
            for i in range(1, num_evses+1):
                for j in range(1, num_connectors+1):
                    connector_values.append((evse_AND_Connectors_ids[f'ConnectorID{i}{j}'], CS_Status, evse_AND_Connectors_ids[f'EVSEID{i}'], Vendor_Id, evse_AND_Connectors_ids[f'Connector{i}{j}_Type'],UserName_details['UserName'],Vendor_Name,))

            insert_statement = "INSERT INTO connector1 (connectorId, connectorStatus, evseId, vendorId, connectorType, userName, vendorName) VALUES (%s, %s, %s, %s, %s,%s,%s)"
            print(connector_values)
            


            for val in connector_values:
                cursor.execute(insert_statement, val)
                print(val)

            connection.commit()
            
            print("connector_values Its worked")
        
            return redirect(url_for('login'))
    else:

        #return render_template('cs_verification.html',Num_EVSE=4, Num_Connectors=4)
        return render_template('cs_verification.html',Num_EVSE=num_evses, Num_Connectors=num_connectors)



@app.route('/cs_authentication')
def cs_authentication():

    return render_template('cs_authentication.html')


@app.route('/ChargingStation', methods=('GET', 'POST'))
  
def ChargingStation():
    session_ID = session.get('sessionID', None)
    print(session_ID)
    if request.method == 'POST':
        selectedVariable = request.form['selectedVariable']
        print(selectedVariable)
        

        cursor.execute("SELECT * FROM chargingstation WHERE vendorName=%s",(selectedVariable,))
        vendor_details = cursor.fetchone()
        print(vendor_details)
        print("vendorDetails")

        
        cursor.execute("SELECT No_of_EVSEs, No_of_Connectors_On_Each_EVSEs FROM chargingstation WHERE vendorName=%s",(selectedVariable,))
        EVSE_Connector_details = cursor.fetchone()
        print(EVSE_Connector_details)
        
        num_Evse=EVSE_Connector_details[0]
        num_Connetors=EVSE_Connector_details[1]
        print(type(num_Evse))
        print(type(num_Connetors))
        num_Evse = int(num_Evse)
        num_Connetors = int(num_Connetors)


        cursor.execute("SELECT * FROM connector1 WHERE vendorName=%s",(selectedVariable,))
        connector_details = cursor.fetchall() 
        print(connector_details)
        print("ChargingStation")
        
        
                
        
        return render_template('ChargingStation.html',num_Evse=num_Evse,num_Connetors= num_Connetors, station_details1=vendor_details, station_details2=connector_details, session_id=session_ID['session_id'])
    else:
        
        return redirect(url_for('station_details', session_id=session_ID['session_id']))



@app.route('/station_details')
def station_details():
    SESSION_ID = request.cookies.get('session_id')
    cursor.execute("SELECT Username FROM cs_registration WHERE Session_Id=%s",(SESSION_ID,))
    Username = cursor.fetchone() 
        
    print(Username[0])
    print("********************")
    if SESSION_ID is not None:
        cursor.execute("SELECT vendorName FROM chargingstation WHERE userName=%s",(Username[0],))
        vendor_details = cursor.fetchall()
        print(vendor_details)
        print("vendorDetails")
                   
    
        return render_template('station_details.html', station_details1=vendor_details, session_id=SESSION_ID)
    else:
        
        OwnerDetails = session.get('Vendor_details', None)
        Vendor_Name=OwnerDetails['Vendor_Name']
        print(Vendor_Name)
        cursor.execute("SELECT userName FROM chargingstation WHERE Vendor_Name=%s", (Vendor_Name,))
        userName = cursor.fetchone()
        print(userName)
        cursor.execute("SELECT Vendor_Name FROM chargingstation WHERE userName=%s",(Username[0],))
        vendor_details = cursor.fetchall()
        print(vendor_details)
        print("vendorDetails")
       

        
        
                   
    
        return render_template('station_details.html', station_details1=vendor_details)



@app.route('/report')
def report():
    SESSION_ID = request.cookies.get('session_id')
    if SESSION_ID is not None:
    
        connection = mysql.connector.connect(host="localhost", port= 3306, user="root", passwd="12345", database="ocpp")
        cursor1 = connection.cursor()


        cursor1.execute("SELECT Username From cs_registration  WHERE Session_Id=%s", (SESSION_ID,))
        Report1 = cursor1.fetchone()
        length_of_values = len(Report1)
        print(length_of_values)
        print("Report Page")
        print(Report1[0])

        cursor1.execute("SELECT vendorName From chargingstation  WHERE userName=%s", (Report1[0],))
        list_of_vendorName = cursor1.fetchall()
        len_of_list_of_vendorName=len(list_of_vendorName)
        print(list_of_vendorName)
        print(len_of_list_of_vendorName)
        
        
        cursor1.execute("SELECT * FROM chargingstation WHERE userName=%s",(Report1[0],))
        vendor_details = cursor1.fetchall()
        vendor_details = vendor_details[::-1]
        
        print(vendor_details)
        print("vendorDetails")
        
        
        cursor1.execute("SELECT * FROM connector1 WHERE userName = %s", (Report1[0],))

        Report2 = cursor1.fetchall()
        print(Report2)
        
        print("Refresh Report")
        
        cursor1.execute("SELECT No_of_Connectors_On_Each_EVSEs, No_of_EVSEs From chargingstation  WHERE userName=%s", (Report1[0],))
        
        NUM_EVSE_Conn = cursor1.fetchall()
        print(NUM_EVSE_Conn)


        
        
        int_list = []

        for values in reversed(NUM_EVSE_Conn):
            int_values = []
            for value in values:
                int_values.append(int(value))
            int_list.append(tuple(int_values))

        print(int_list)
        print("List of Conn and EVSEs")
        
       
       
       


        print(type(NUM_EVSE_Conn))
        Connector_number = NUM_EVSE_Conn[0][0]
        Evse_number = NUM_EVSE_Conn[0][1]
        Evse_number = int(Evse_number)
        Connector_number = int(Connector_number)
       #peint(length_of_values)
        #for num in Report2:
        #    print(num)
        print(Report2)
        cursor1.close()
        
        
        #connectorId connectorStatus  evseId  vendorId  connectorType
        # Pass the updated data to the template
        
        return render_template('report.html', len_of_list_of_vendorName=len_of_list_of_vendorName, NUM_EVSE_Conn=int_list,  station_details1=vendor_details, station_details2=Report2,session_id=SESSION_ID)
    
   



@app.route('/status', methods=('GET', 'POST'))
def status():
    session_ID = request.cookies.get('session_id')
    print(session_ID)
    print("status Worked")
    if request.method == 'POST':
        selectedVariable = request.form['selectedVariable_2']
        print(selectedVariable)
        

        cursor.execute("SELECT * FROM chargingstation WHERE vendorName=%s",(selectedVariable,))
        vendor_details = cursor.fetchone()
        print(vendor_details)
        print("vendorDetails")

        
        cursor.execute("SELECT No_of_EVSEs, No_of_Connectors_On_Each_EVSEs FROM chargingstation WHERE vendorName=%s",(selectedVariable,))
        EVSE_Connector_details = cursor.fetchone()
        print(EVSE_Connector_details)
        
        num_Evse=EVSE_Connector_details[0]
        num_Connetors=EVSE_Connector_details[1]
        print(type(num_Evse))
        print(type(num_Connetors))
        num_Evse = int(num_Evse)
        num_Connetors = int(num_Connetors)


        cursor.execute("SELECT * FROM connector1 WHERE vendorName=%s",(selectedVariable,))
        connector_details = cursor.fetchall() 
        print(connector_details)
        print("ChargingStation")
        
        
                
        
        return render_template('status.html',num_Evse=num_Evse,num_Connetors= num_Connetors, station_details1=selectedVariable, station_details2=connector_details, session_id=session_ID)



@app.route('/payment_details')
def payment_details():
    SESSION_ID = request.cookies.get('session_id')
    print(SESSION_ID)
    if SESSION_ID is not None:
        cursor.execute("SELECT Username FROM cs_registration WHERE Session_Id=%s",(SESSION_ID,))
        Username = cursor.fetchone()
        print(Username)

        cursor.execute("SELECT * FROM payment_details WHERE userName=%s",(Username[0],))
        payment_details = cursor.fetchall()
        print(payment_details)
        num_rows = len(payment_details)
    
        return render_template('payment_details.html',num_rows=num_rows, payment_details=payment_details,session_id=SESSION_ID)
    else:
        return "Session ID is In Valid"




@app.route('/energy_rate_card')
def energy_rate_card_details():
    SESSION_ID = request.cookies.get('session_id')
    print(SESSION_ID)
    print("we get")
    if SESSION_ID is not None:
        cursor.execute("SELECT Username FROM cs_registration WHERE Session_Id=%s",(SESSION_ID,))
        Username = cursor.fetchone()
        print(Username[0])

        cursor.execute("SELECT * FROM energy_rate_card_details WHERE userName=%s",(Username[0],))
        energy_rate_card_details = cursor.fetchone()
        print("Why")
        print(energy_rate_card_details)
        return render_template('energy_rate_card.html', energy_rate_card_details=energy_rate_card_details,session_id=SESSION_ID)



@app.route('/bookings')
def bookings_details():
    SESSION_ID = request.cookies.get('session_id')
    
    return render_template('bookings.html',session_id=SESSION_ID)















 # Define the API endpoint
@app.route('/set_variable', methods=('POST', 'GET'))
def set_variable():
    #while True:
    if request.method == 'GET':
    # Define the URL of the receiving Flask application
        
        url = 'http://10.81.21.16:5000/receive_message' 
        #url = 'http://127.0.0.1:5000/receive_variable'  
        print("This line worked 1")
        headers = {'Content-type': 'application/json'}
        #data={'message':'Hellow'}
        UPDATE_DETAILS = session.get('Update_CS_Details', None)
        #data = session.get('VendorID_Details', None)
               
        print(UPDATE_DETAILS)
        #print(data)
       
       # print(VENDER_ID_DETAILS)
        
        response = requests.post(url, json=UPDATE_DETAILS, headers=headers, timeout=10)
        if response.status_code == 200:

            response_json = response.json()# Access the response JSON data

            print(f"response:{response_json}")# Print the response JSON data

            return 'Variable sent'
            
        return redirect(url_for('home'))
   
    return 'Variable Not sent'






@app.route('/getVariables', methods=('GET', 'POST'))
def getVariables():
    SESSION_ID = request.cookies.get('session_id')
    if request.method == 'POST':
        Vendor_Id = request.form['vendorId']
        categories = request.form['categories[]']
        print(Vendor_Id)
        print(categories)

        
        variables_dict = {}
        variables_list = categories.split(',')

        variables_dict['variables'] = variables_list
        variables_dict['vendorId'] = Vendor_Id
        print(variables_dict)
        session['Variables_On_CS']=variables_dict

       
        
        return redirect(url_for('getVariables_request', session_id=SESSION_ID))
        
        
    return render_template('getVariables.html',session_id=SESSION_ID)



@app.route('/getVariables_request', methods=('POST', 'GET'))
def getVariables_request():
    
        
    if request.method == 'GET':
    # Define the URL of the receiving Flask application
        print("getVariable Request")
        
        url = 'http://10.81.21.2:5000/get_variables_message' 
        #url = 'http://127.0.0.1:5000/receive_variable'  
        print("This line worked 1")
        headers = {'Content-type': 'application/json'}
        
        
        data = session.get('Variables_On_CS', None)
        print(data)     
        
        print(data)
       
       # print(VENDER_ID_DETAILS)
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(response)
        if response.status_code == 200:

            response_json = response.json()# Access the response JSON data

            print(f"response:{response_json}")# Print the response JSON data

            return 'Variable sent'
            
        return redirect(url_for('home'))
        



 



@app.route('/update', methods=('GET', 'POST'))
def update():
    SESSION_ID = request.cookies.get('session_id')
    if request.method == 'POST':
        Vendor_Id = request.form['vendorId']
        Model = request.form['model']
        FirmwareVersion = request.form['firmwareVersion']
        CS_Status = request.form['CS_Status']

        session['Update_CS_Details'] = {}
        

        if (Vendor_Id !=''):
            session['Update_CS_Details']= {'vendorId':Vendor_Id}

        if (Model !=''):
            session['Update_CS_Details']['Model'] = Model
            
    
        if (FirmwareVersion !=''):
            session['Update_CS_Details']['FirmwareVersion'] = FirmwareVersion
            

        if (CS_Status !=''):
            session['Update_CS_Details']['CS_Status'] = CS_Status
        
        return redirect(url_for('set_variable', session_id=SESSION_ID))
        
        
    return render_template('update.html',session_id=SESSION_ID)

  
@app.route('/get_status', methods=('POST','GET'))
def get_status():
    if request.method == 'POST':
        data=request.get_json()

        variable = data

        print('Received message:', variable)
        
  
        cursor.execute("SELECT * FROM connector1 WHERE vendorId = %s", (variable['vendorId'],))
        row = cursor.fetchall()
        session['Conn_Status'] = row
        print(session['Conn_Status'])
        
        
        return "ok"
    return "Not Ok"
    #redirect(url_for('report'))
        








@app.route('/UserSignup', methods=('GET', 'POST'))
def UserSignup():
    if request.method == 'POST':
          # Get form data
        UserName = request.form['userName']
        Password    = request.form['password']
        Email    = request.form['email']
        Registered_Mobile_Number = request.form['phoneNumber']
        Address = request.form['address']
        EV_Number = request.form['evNO']
        Year_Of_Manf=request.form['yearOfManf']
        Charging_Capacity=request.form['chargingCapacity']
        License=request.form['license']
        
        
        
        cursor.execute("SELECT * FROM user_registration WHERE Username=%s", (UserName,))
        user = cursor.fetchone()
        if user is None:
            # No matching row was found

                cursor.execute("SELECT MAX(User_ID) FROM user_registration")
                result = cursor.fetchone()
                result= result[0]
                
                if result is not None:
                    last_id = result
                else:
                     last_id = 0

                # Increment the ID by 1
                new_id = last_id + 1


                cursor.execute("INSERT INTO user_registration (User_ID, Username, Password, Email, Mobile_Number, Address) VALUES (%s, %s, %s, %s, %s, %s)", (new_id, UserName, Password, Email, Registered_Mobile_Number, Address,))
                connection.commit()
                

                
            
                cursor.execute("SELECT * FROM user_registration WHERE Username=%s",(UserName,))
                UserID=cursor.fetchone()   
                print(UserID)

                

                cursor.execute("INSERT INTO user_ev_details (User_ID, EV_Number, Year_Of_Manf, Charging_Capacity, License) VALUES (%s, %s, %s, %s, %s)", (UserID[0], EV_Number, Year_Of_Manf, Charging_Capacity, License))

                connection.commit()    
        return redirect(url_for('UserLogin'))
    else:
            
        return render_template('UserSignup.html')






@app.route('/UserLogin', methods=('GET', 'POST'))
def UserLogin():
    if request.method == 'POST':
          # Get form data
        Email = request.form['email']
        Password = request.form['password']
        session['User_Login_credentials'] = {'Email': Email, 'Password': Password}
        print(session['User_Login_credentials'])
        
        cursor.execute("SELECT * FROM user_registration WHERE Email=%s", (Email,))
        user = cursor.fetchone()
         
        if user is None:
        
            message="Please provide valid Email and password"
            return render_template('Userlogin.html', message=message)
           
        elif user[2] == Password:        
            session_id=str(uuid.uuid4())
            
            
            
            cursor.execute("UPDATE user_registration SET Session_Id=%s WHERE Email=%s", (session_id, Email,))
            connection.commit()
            print(session_id)
            
            

            # The password matches, so redirect to the home page
            
            resp = make_response(redirect(url_for('UserHome',session_id=session_id)))
            expires_date = datetime.datetime.now() + datetime.timedelta(days=7)  
            resp.set_cookie('user_session_id', session_id, expires=expires_date)
            return resp      
        else:
            message="The password does not match"
         
            return render_template('Userlogin.html', message=message)
            
    return render_template('UserLogin.html')  




@app.route('/UserHome')
def UserHome():
          
        User_session_id = request.cookies.get('user_session_id')
        if User_session_id is not None:
            cursor.execute("SELECT Username FROM user_registration WHERE Session_Id=%s", (User_session_id,))
            username = cursor.fetchone()
            
        
            return render_template('UserHome.html', username=username, User_session_id=User_session_id)
    
    




@app.route('/UserCharging_station_details',methods=('GET','POST'))
def UserCharging_station_details():
    User_session_id = request.cookies.get('user_session_id')
    if request.method == 'GET':
        
        cursor.execute("SELECT DISTINCT cs_registration.Vendor_Name,cs_registration.Location FROM cs_registration INNER JOIN connector1 ON cs_registration.Vendor_Id = connector1.vendorId WHERE connectorStatus='Available'")
        available_cs =  cursor.fetchall() 
        print(available_cs)
        cursor.execute("SELECT User_ID FROM user_registration  WHERE Session_Id = %s", (User_session_id,))
        User_ID = cursor.fetchone()
        session['User_ID'] = {'User_ID': User_ID}

        return render_template('UserCharging_station_details.html', CS_details=available_cs, User_session_id=User_session_id)
    
@app.route('/UserSelect_station',methods=('GET','POST'))
def UserSelect_station():
    selected_station = request.form['station']
    session['selectedCS'] = {'selectedCS': selected_station}
    return redirect(url_for('UserReservation'))
    


    
        
@app.route('/UserReservation',methods = ('GET','POST'))
def UserReservation():
    
    selectedCS_details = session.get('selectedCS', None)
    
    print(selectedCS_details)
    print("reservation")
          
    cursor.execute("SELECT Vendor_Id FROM cs_registration  WHERE Vendor_Name = %s", (selectedCS_details['selectedCS'],))
    Vendor_Id = cursor.fetchone()
        
    cursor.execute("SELECT DISTINCT Vendor_Id,Vendor_Name,Location,evseId,connectorId,Price FROM cs_registration JOIN connector1 ON cs_registration.Vendor_Id = connector1.vendorId WHERE connector1.connectorStatus = 'Available' AND connector1.vendorId = %s",(Vendor_Id[0],))
    result = cursor.fetchall()
    print(result)
    
    
    
    return render_template('UserReservation.html', a = result)

@app.route('/UserReservation_details', methods=('POST','GET'))
def UserReservation_details():
    
    User_ID = session.get('User_ID', None)

    CS_id = request.form.get('cs-id')
    CS_name = request.form.get('cs-name')
    Location = request.form.get('cs-Location')
    evse = request.form.get('evse')
    connector = request.form.get('connector')
    prise = request.form.get('cs-prise')
    
    print(evse)
    print(connector)

    session['selecting_cs_details'] = {'User_ID':User_ID,'vendorId': CS_id, 'vendorName':CS_name, 'Location':Location, 'evse':evse, 'connector':connector, 'prise':prise}
    print(session['selecting_cs_details'])
    print("reservation_details")
    return redirect(url_for('UserSelect_slots_details'))









@app.route('/UserSelect_slots_details', methods=('POST','GET'))
def UserSelect_slots_details():
    selected_timeSlot = session.get('selecting_cs_details', None)
    print(selected_timeSlot)
    values = tuple(selected_timeSlot.values())
    print(values)
    if request.method == 'GET':
        cursor.execute("SELECT slot FROM time_slots WHERE slot NOT IN (SELECT time_slots FROM ev_idtoken WHERE vendor_id = %s)", (selected_timeSlot['vendorId'],))
        Available_slots = cursor.fetchall()
        print(Available_slots)
        print(selected_timeSlot)
        return render_template('UserSelect_slots_details.html', a = values, slot=Available_slots)


@app.route('/UserSelect_slots', methods=('POST','GET'))
def UserSelect_slots():
        user_id = request.form.get('user-id')
        cs_id = request.form.get('cs-id')
        cs_name = request.form.get('cs-name')
        cs_Location = request.form.get('cs-Location')
        
        evse = request.form.get('evse')
        connector = request.form.get('connector')
        prise = request.form.get('prise')
        timeslot = request.form.get('timeslots')

        
        print('timeslot', timeslot)
        session['Reservation_Details'] = {'user_id':user_id, 'vendorId':cs_id, 'vendorName':cs_name,'cs_Location':cs_Location, 'evse': evse, 'connector':connector,'prise':prise,  'timeslot':timeslot}
        return redirect(url_for('UserRequest_for_resevation'))
    



    


@app.route('/UserRequest_for_resevation',methods = ('POST','GET'))
def UserRequest_for_resevation():
    Reservation_Details = session.get('Reservation_Details', None)
    if request.method == 'GET':
        url = 'http://127.0.0.1:5000/reservation_details_message'

        print("This line worked 1")
        data = Reservation_Details
        headers = {'Content-type':'application/json'}

        print(data)
        print("Worked ")
        response = requests.post(url,json=data,headers=headers)
        print(response.status_code)
        #For testing 
        response="1"
        #response.status_code=200
        session['Reservation_ID'] = {'Reservation_id': response}
        return redirect(url_for('UserReserved_cs_details'))
        ##above code for Testing 
        #if response.status_code == 200:
          #  response_json = response.json()

          #  print(f"response:{response_json}")

            #return redirect(url_for('reserved_cs_details'))
        #else:
         #   print('Error:', response.status_code)

          #  return 'Error: ' + str(response.status_code)
    print(response)


    return "this function method is POST"






@app.route('/UserReserved_cs_details',methods = ('GET','POST'))
def UserReserved_cs_details():
    Reservation_id = session.get('Reservation_ID', None)
    if request.method == 'GET':
        cursor.execute("SELECT * FROM ev_idtoken WHERE reservation_id=%s", (Reservation_id['Reservation_id'],))
        Reservation_Details = cursor.fetchall()
        print(Reservation_Details)
        #print(ans)
        #return "ok"
        return render_template('UserReserved_cs_details.html',Reservation_Details = Reservation_Details)
    











@app.route('/UserEdit_reservation',methods = ('GET','POST'))
def UserEdit_reservation():
    if request.method == 'POST':
        Reason = request.form['reason']
        print(Reason)
        parameters = request.form['parameters']
        print(parameters)
        session['edit_reservation'] = {'Reason': Reason, 'parameters':parameters}
        return redirect(url_for('UserRequest_for_modify_resevation_details')) 
    return render_template('UserEdit_reservation.html')


@app.route('/UserRequest_for_modify_resevation_details',methods = ('POST','GET'))
def UserRequest_for_modify_resevation_details():
    edit_reservation_details = session.get('edit_reservation', None)
    if request.method == 'GET':
        url = 'http://127.0.0.1:5000/reservation_details_message'

        print("This line worked 1")
        data = edit_reservation_details
        headers = {'Content-type':'application/json'}

        print(data)
        print("Worked2 ")
        response = requests.post(url,json=data,headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            response_json = response.json()

            print(f"response:{response_json}")

            return 'Variable sent'
        else:
            print('Error:', response.status_code)

            return 'Error: ' + str(response.status_code)
    print(response)


    return "this function method is POST"

    
    
    
@app.route('/UserCancellation',methods = ('GET','POST'))
def UserCancellation():
    if request.method == 'POST':
        Reason = request.form['reason']
        print(Reason)
        OTP = request.form['otp']
        print(OTP)
        session['EVreservation_cancel'] = {'Reason': Reason, 'OTP':OTP}
        return redirect(url_for('UserRequest_for_reservation_cancellation')) 
    return render_template('UserCancellation.html')





@app.route('/UserRequest_for_reservation_cancellation',methods = ('POST','GET'))
def UserRequest_for_reservation_cancellation():
    EVreservation_cancel = session.get('EVreservation_cancel', None)
    if request.method == 'GET':
        url = 'http://127.0.0.1:5000/reservation_details_message'

        print("request_for_reservation_cancellation")
        data = EVreservation_cancel
        headers = {'Content-type':'application/json'}

        print(data)
        print("Worked2 ")
        response = requests.post(url,json=data,headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            response_json = response.json()

            print(f"response:{response_json}")

            return 'Variable sent'
        else:
            print('Error:', response.status_code)

            return 'Error: ' + str(response.status_code)
    print(response)


    








@app.route('/UserPayment-details',methods = ('GET','POST'))
def UserPayment_details():
    if request.method == 'GET':
        return render_template('UserPayment-details.html')



    
@app.route('/UserBookings',methods = ('GET','POST'))
def UserBookings():
    User_session_id_For_booking = request.cookies.get('user_session_id')
    if request.method == 'GET':
        cursor.execute("SELECT user_id FROM user_registration WHERE Session_Id=%s", (User_session_id_For_booking,))
        userID = cursor.fetchall()
        print(userID)
        cursor.execute("SELECT * FROM ev_idtoken WHERE user_id=%s", (userID[0][0],))
        Booking_Details = cursor.fetchall()

        return render_template('UserBookings.html', Booking_Details=Booking_Details)


 


@app.route('/Clint_logOut', methods=('POST','GET'))
def Clint_logOut():

    resp = make_response(redirect(url_for('login_redirect')))
    resp.set_cookie('session_id', expires=0)
    return resp

@app.route('/User_logOut', methods=('POST','GET'))
def User_logOut():

    resp = make_response(redirect(url_for('login_redirect')))
    resp.set_cookie('user_session_id', expires=0)
    return resp

if __name__ == '__main__':
    #app.run(host= '0.0.0.0', port= 5000, debug=True)
    app.run(host='0.0.0.0', port=5000)
    
