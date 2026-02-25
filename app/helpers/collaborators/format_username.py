def format_username(username, firstname, lastname):
    if username == "" or not username:
        username = f"{firstname.lower().strip().replace(" ","")}.{lastname.lower().strip().replace(" ","")}"
    
    else:
        username = username.lower().strip().replace(" ","")