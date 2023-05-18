from flask import * 
import mysql.connector
import uuid
import datetime
from flask import Flask, request, jsonify
import logging
import requests

#Flask, render_template, request, redirect, url_for

# MySQL configurations
connection = mysql.connector.connect(host="35.77.214.112", port= 3306, user="root", passwd="root1", database="ocpp")
cursor = connection.cursor()

app = Flask(__name__)    #This creates a new Flask application instance, named app.

app.secret_key = "supersecretkey" #This sets the secret key for the Flask application. The secret key is used to encrypt session data, and should be kept secret and secure.







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
        
        
        cursor.execute("SELECT * FROM user_registration WHERE Email=%s", (Email,))
        user = cursor.fetchone()
         
        if user is None:
        
            message="Please provide valid Email and password"
            return render_template('Userlogin.html', message=message)
           
        elif user[2] == Password:        
            session_id=str(uuid.uuid4())
            
            
            
            cursor.execute("UPDATE user_registration SET Session_Id=%s WHERE Email=%s", (session_id, Email,))
            connection.commit()
            
            

            # The password matches, so redirect to the home page
            
            resp = make_response(redirect(url_for('home',session_id=session_id)))
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
    
@app.route('/Userselect_station',methods=('GET','POST'))
def Userselect_station():
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
        return redirect(url_for('reserved_cs_details'))
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


if __name__ == '__main__':
    app.run(debug=True)