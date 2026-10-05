from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import requests
import textwrap
import subprocess
from bs4 import BeautifulSoup
import re
import json
import os

class Turtle:
    def __init__(self, name, common_name, taxon_id, rank, wiki_url, photo_url):
        self.__name = name
        self.__common_name = common_name
        self.__taxon_id = taxon_id
        self.__rank = rank
        self.__wiki_url = wiki_url
        self.__photo_url = photo_url

    @property
    def name(self):
        return self.__name

    @property
    def common_name(self):
        return self.__common_name

    @property
    def taxon_id(self):
        return self.__taxon_id

    @property
    def rank(self):
        return self.__rank

    @property
    def wiki_url(self):
        return self.__wiki_url

    @property
    def photo_url(self):
        return self.__photo_url


current_account = ""

def make_request(url,params=None,headers=None):
    try:
        response = requests.get(
            url, params=params,headers=headers,timeout = 10)
        response.raise_for_status()
    except  requests.exceptions.ConnectionError:
        messagebox.showerror(
            "Connection Error",
            "Could not connect to the server. Please check your internet connection.")
        return
    except requests.exceptions.Timeout:
        messagebox.showerror(
            "Timeout Error",
            "The server took too long to respond. Please try again.")
        return
    except requests.exceptions.HTTPError:
        messagebox.showerror(
            "HTTP Error",
            "The server returned an HTTP error. Please try again later.")
        return
    except requests.exceptions.RequestException:
        messagebox.showerror(
            "Request Error",
            "An error occurred while sending the request.")
        return
    return response
def turtle_wiki(search_query):
    autocomplete_response = make_request("https://api.inaturalist.org/v2/taxa/autocomplete", {"q": search_query})
    if autocomplete_response is None:
        return
    try:
        autocomplete_data = autocomplete_response.json()
    except ValueError:
        messagebox.showerror(
            "Data Error",
            "The server returned invalid data.")
        return
    if not autocomplete_data["results"]:
        messagebox.showerror(
            "Data Error",
            "The server returned an empty result."
        )
        return
    taxon_id = autocomplete_data["results"][0]["id"]
    taxon_response = make_request(f"https://api.inaturalist.org/v1/taxa/{taxon_id}",
                             {"fields": "name,rank"
                             ",preferred_common_name,"
                             "wikipedia_url,default_photo"})
    if taxon_response is None:
        return
    try:
        taxon_data = taxon_response.json()
    except ValueError:
        messagebox.showerror(
            "Data Error",
            "The server returned invalid data.")
        return
    if not taxon_data["results"]:
        messagebox.showerror(
            "Data Error",
            "The server returned an empty result.")
        return
    turtle_info = taxon_data["results"][0]
    taxon_id = turtle_info["id"]
    if "name" not in turtle_info or turtle_info["name"] is None:
        messagebox.showerror("Data Error","The server did not provide a species name.")
        return
    name = turtle_info["name"]
    if "rank" not in turtle_info or turtle_info["rank"] is None:
        messagebox.showerror("Data Error", "The server did not provide a species rank.")
        return
    rank = turtle_info["rank"]
    if "preferred_common_name" not in turtle_info or turtle_info["preferred_common_name"] is None:
        messagebox.showerror("Data Error", "The server did not provide a common name for this species.")
        return
    common_name = turtle_info["preferred_common_name"]
    if "wikipedia_url" not in turtle_info or turtle_info["wikipedia_url"] is None:
        messagebox.showerror("Data Error", "The server did not provide wikipedia url for this species.")
        return
    wiki_url = turtle_info["wikipedia_url"]
    if not wiki_url:
        messagebox.showerror("Wikipedia Error",
         "Wikipedia page is not available for this species.")
        return
    wiki_url = wiki_url.replace(" ", "_")
    default_photo = turtle_info.get("default_photo")
    if default_photo is None:
        messagebox.showerror(
            "Photo Error",
            "No photo is available for this turtle species.")
        return

    photo_url = default_photo.get("medium_url")
    if photo_url is None:
        messagebox.showerror(
            "Photo Error",
            "The turtle photo URL is not available.")
        return

    turtle = Turtle(name, common_name, taxon_id, rank, wiki_url, photo_url)
    wikipedia_response = make_request(wiki_url,headers={"User-Agent": "SpeciesInfoProject/1.0"})
    if wikipedia_response is None:
        return
    wikipedia_response = wikipedia_response.text
    soup = BeautifulSoup(wikipedia_response, "html.parser")
    article = soup.find("div", class_="mw-parser-output")
    if article is None:
        messagebox.showerror(
            "Wikipedia Error",
            "Could not find the required information on Wikipedia.")
        return
    paragraphs = article.find_all("p")
    summary_text = ""
    for paragraph in paragraphs:
        text = paragraph.get_text()
        summary_text += text + "\n"
    summary_text = re.sub(r"\[\d+]", "", summary_text)
    return (f"Wikipedia summary - {summary_text}"), turtle

def find_turtle():
    search_query = search_entry.get()
    if search_query == "" or search_query.isspace():
        messagebox.showerror("Empty_Search_Field_Error", "Search input field is empty!")
        return

    result = turtle_wiki(search_query)
    if result is None:
        return
    wiki_summary, turtle = result
    turtle_details = (f"Scientific name - {turtle.name}\n\n"
         f"Rank - {turtle.rank}\n\n"
         f"Common name - {turtle.common_name}\n\n"
         f"Taxon id - {turtle.taxon_id}\n\n"
         f"Wikipedia url - {turtle.wiki_url}\n\n")

    image_response = make_request(turtle.photo_url)

    if image_response is None:
        return

    image_data = image_response.content

    with open("turtle.jpg", "wb") as file:
        file.write(image_data)
    try:
        subprocess.run(
            ["ImageMagick/magick.exe", "turtle.jpg", "turtle.png"],
            check=True
        )
    except FileNotFoundError:
        messagebox.showerror(
            "File Error",
            "ImageMagick is not installed or is not added to PATH."
        )
        return
    except subprocess.CalledProcessError:
        messagebox.showerror(
            "File Error",
            "Image processing failed."
        )
        return
    try:
        turtle_photo_image = PhotoImage(file="turtle.png")
    except TclError:
        messagebox.showerror("ImageLoadError"
                             ,"Could not load the turtle image.")
        return

    root2 = Toplevel(root1)
    root2.title(search_query)
    root2.state("zoomed")
    root2.iconphoto(False, app_icon_image)
    root2.resizable(True, True)

    canvas = Canvas(root2)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(root2, command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    frame = ttk.Frame(canvas)

    canvas.create_window((0, 0), window=frame, anchor="nw", width=1540)

    frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

    result_title_label = ttk.Label(frame, text=(f"Result of searching about {search_query}"), anchor="center", font=("Georgia", 30, "bold"), wraplength=1000,
                              foreground="blue", background="yellow")
    result_title_label.pack(anchor="n", fill="x", expand=True, padx=50, pady=20)


    turtle_image_label = ttk.Label(frame, image=turtle_photo_image)
    turtle_image_label.pack(anchor="nw", padx=20, pady=(50, 0))
    turtle_image_label.image = turtle_photo_image


    turtle_details_label = ttk.Label(frame,text = turtle_details)
    turtle_details_label.pack(padx=20, pady=(50, 0),anchor="nw",expand = True)
    turtle_details_label.config(font = ("Arial", 10, "bold"))


    wiki_summary = textwrap.fill(wiki_summary, width=150)

    summary_label = ttk.Label(frame, text=wiki_summary)
    summary_label.pack(padx=20, pady=20)
    summary_label.config(font = ("Arial", 15, "bold"),background="olive",foreground="white")

    frame.update_idletasks()

    canvas.configure(scrollregion=canvas.bbox("all"))
    users[current_account]["history"].append(search_query)

    with open("users", "w") as file:
        json.dump(users, file, indent=4)

def open_registration_frame():
    login_frame.place_forget()
    registration_frame.place(x=0, y=0, width=1000, height=700)

    login_entry.delete(0, "end")
    password_entry.delete(0, "end")

    registration.place(x=380, y=10, height=50)

    login_registration.place(x=0, y=100, height=50)

    password_registration.place(x=0, y=150, height=50)

    login_registration_entry.place(x=150, y=100, height=50)

    password_registration_entry.place(x=150, y=150, height=50)

    show_password_button.place(x=375, y=150, height=50, width=150)

    signin_registration_button.place(x=700, y=100, height=50)

    return_to_login_button.place(x=700, y=150, height=50)

    registration_image_label.place(x=200, y=270)

def return_to_login():
    registration_frame.place_forget()
    login_frame.place(x=0, y=0, width=1000, height=700)


def account_append():
    login_registration = login_registration_entry.get().lower()
    password_registration = password_registration_entry.get()

    if login_registration == "" or login_registration.isspace():
        messagebox.showerror("Empty_Login_Error", "Login input field is empty!")
        return
    if password_registration == "" or password_registration.isspace():
        messagebox.showerror("Empty_Password_Error", "Password input field is empty!")
        return
    if len(login_registration) < 4:
        messagebox.showerror(
            "Short_Login_Error",
            "Login must contain at least 4 characters!"
        )
        return

    if len(password_registration) < 4:
        messagebox.showerror(
            "Short_Password_Error",
            "Password must contain at least 4 characters!"
        )
        return
    if login_registration in users:
        messagebox.showerror("Taken_Login_Error", " That username is already taken!")
        return
    users[login_registration] = {"password": password_registration, "history": []}
    with open("users", "w") as file:
        json.dump(users, file, indent=4)
        messagebox.showinfo("Successful Sign in", "You successfully signed up!")

    login_registration_entry.delete(0, "end")
    password_registration_entry.delete(0, "end")


def hide_password_registration():
    password_registration_entry.config(show="*")
    show_password_button.config(text="Show password", command=show_password_registration)


def show_password_registration():
    password_registration_entry.config(show="")
    show_password_button.config(text="Hide Password", command=hide_password_registration)


def hide_password_login():
    password_entry.config(show="*")
    show_password_button_login.config(text="Show Password", command=show_password_login)


def show_password_login():
    password_entry.config(show="")
    show_password_button_login.config(text="Hide Password", command=hide_password_login)


def open_search_frame():
    login = login_entry.get().lower()
    password = password_entry.get()
    login_entry.delete(0, "end")
    password_entry.delete(0, "end")
    if login == "" or login.isspace():
        messagebox.showerror("Empty_Login_Error", "Login input field is empty!")
        return
    if password == "" or password.isspace():
        messagebox.showerror("Empty_Password_Error", "Password input field is empty!")
        return

    if login not in users:
        messagebox.showerror("Login_Error", "That username does not exist!")
        return
    if users[login]["password"] == password:
        messagebox.showinfo("Successful logging!", "You have logged into your account")
        global current_account
        current_account = login
        login_frame.place_forget()
        search_frame.place(x=0, y=0, width=1000, height=700)
    else:
        messagebox.showerror("Password_Error", "Incorrect Password!\nEnter correct one")


def open_search():
    profile_frame.place_forget()
    search_frame.place(x=0, y=0, width=1000, height=700)


def open_login():
    global current_account
    current_account = ""

    profile_frame.place_forget()
    login_frame.place(x=0, y=0, width=1000, height=700)

def open_profile():
    request_history = "\n".join(users[current_account]["history"])
    search_frame.place_forget()
    profile_frame.place(x=0, y=0, width=1000, height=700)

    profile_login_text.place(x=0, y=100, height=50)

    request_count_text.place(x=0, y=175, height=50)

    change_account_profile_button.place(x=300, y=100, height=50)

    return_to_login_profile_button.place(x=300, y=150, height=50)

    clear_history.place(x=500, y=150, height=50, width=150)

    request_history_text.place(x=0, y=250)

    profile_image_label.place(x=350, y=270)

    profile_login = current_account
    request_count = len(users[current_account]["history"])

    profile_login_text.config(text=f"Login - {profile_login}")
    request_count_text.config(text=f"Request count - {request_count}")
    request_history_text.config(text=f"Request history:\n{request_history}")

def delete_history():
    users[current_account]["history"].clear()
    with open("users", "w") as file:
        json.dump(users, file, indent=4)

    request_history_text.config(text = "Request history - \n")
    request_count_text.config(text = "Request count - 0\n")


users = {}

if os.path.exists("users"):
    with open("users", "r") as file:
        users = json.load(file)
else:
    with open("users", "w") as file:
        json.dump(users, file, indent=4)


root1 = Tk()
root1.title("Turtle-Wiki")
screenwidth = root1.winfo_screenwidth()
screenheight = root1.winfo_screenheight()
x = (screenwidth - 1000) // 2
y = (screenheight - 700) // 2
root1.geometry(f"1000x700+{x}+{y}")
root1.configure(bg="#F4F6F8")
app_icon_image = PhotoImage(file="turtle_ico.png")
root1.iconphoto(False, app_icon_image)
root1.resizable(False, False)

login_frame = ttk.Frame(root1)
login_frame.place(x=0, y=0, width=1000, height=700)

program_text = ttk.Label(login_frame, text="Turtle - Wiki", foreground="blue", font=("Arial", 20, "bold"), anchor="n")
program_text.place(x=380, y=10, height=50)

login_text = ttk.Label(login_frame, text="Login", font=("Arial", 15, "bold"))
login_text.place(x=0, y=100, height=50)

password_text = ttk.Label(login_frame, text="Password", font=("Arial", 15, "bold"))
password_text.place(x=0, y=150, height=50)

login_entry = ttk.Entry(login_frame, font=("Arial", 15, "bold"))
login_entry.place(x=150, y=100, height=50)

password_entry = ttk.Entry(login_frame, font=("Arial", 15, "bold"), show="*")
password_entry.place(x=150, y=150, height=50)

login_button = ttk.Button(login_frame, text="Log in", command=open_search_frame)
login_button.place(x=148, y=200, height=50, width=230)

show_password_button_login = ttk.Button(login_frame, text="Show Password", command=show_password_login)
show_password_button_login.place(x=375, y=150, height=50, width=150)

not_registered_text = ttk.Label(login_frame, text="You are not Registered?", background="pink", foreground="black")
not_registered_text.place(x=700, y=100, height=50)

signin_button = ttk.Button(login_frame, text="Sign in", command=open_registration_frame)
signin_button.place(x=700, y=150, height=50)

login_image = PhotoImage(file="turtle_image.png")
login_image_label = ttk.Label(login_frame, image=login_image)
login_image_label.image = login_image
login_image_label.place(x=290, y=270)

search_frame = ttk.Frame(root1)

search_title_label = ttk.Label(search_frame, text="Search", font=("Arial", 30, "bold"), foreground="blue")
search_title_label.place(x=380, y=10, height=50)

search_entry = ttk.Entry(search_frame, font=("Arial", 15, "bold"))
search_entry.place(x=100, y=150, width=250, height=30)

search_prompt_label = ttk.Label(search_frame, text="Enter turtle species to find:", width=30, font=("Arial", 10, "bold"))
search_prompt_label.place(x=100, y=50, height=100)

search_button = ttk.Button(search_frame, text="Find info", command=find_turtle)
search_button.place(x=100, y=200, width=150, height=50)

search_image = PhotoImage(file="sulcata_image.png")
search_image_label = ttk.Label(search_frame, image=search_image)
search_image_label.pack(padx=20, pady=(20, 0))
search_image_label.place(x=200, y=270)
search_image_label.image = search_image

show_profile_button = ttk.Button(search_frame, text="Profile", command=open_profile)
show_profile_button.place(x=500, y=200, width=150, height=50)

registration_frame = ttk.Frame(root1)

login_registration_entry = ttk.Entry(registration_frame, font=("Arial", 15, "bold"))

password_registration_entry = ttk.Entry(registration_frame, font=("Arial", 15, "bold"), show="*")

show_password_button = ttk.Button(registration_frame, text="Show Password", command=show_password_registration)

profile_frame = ttk.Frame(root1)

profile_title = ttk.Label(profile_frame, text="Profile", font=("Arial", 30, "bold"), foreground="blue")
profile_title.place(x=350, y=0, height=100)

registration = ttk.Label(registration_frame, text="Registration", foreground="blue", font=("Arial", 20, "bold"),
                             anchor="n")
login_registration = ttk.Label(registration_frame, text="Login", font=("Arial", 15, "bold"))

password_registration = ttk.Label(registration_frame, text="Password", font=("Arial", 15, "bold"))

signin_registration_button = ttk.Button(registration_frame, text="Sign in", command=account_append)

return_to_login_button = ttk.Button(registration_frame, text="Return To Main Menu", command=return_to_login)





registration_image = PhotoImage(file="sulcata_image.png")

registration_image_label = ttk.Label(registration_frame, image=registration_image)

registration_image_label.image = registration_image

change_account_profile_button = ttk.Button(profile_frame, text="Return to login", command=open_login)

return_to_login_profile_button = ttk.Button(profile_frame, text="Return to search menu", command=open_search)

clear_history = ttk.Button(profile_frame, text="Clear history", command=delete_history)

profile_login_text = ttk.Label(profile_frame, font=("Arial", 15, "bold"))

request_count_text = ttk.Label(profile_frame, font=("Arial", 15, "bold"))

request_history_text = ttk.Label(profile_frame, font=("Arial", 15, "bold"), justify="left")

profile_image = PhotoImage(file="sulcata_image.png")
profile_image_label = ttk.Label(profile_frame, image=profile_image)
profile_image_label.image = profile_image

root1.mainloop()
