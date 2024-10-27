import requests
import sys
import json
import time
import re

def send_query(text):
    url = "http://localhost:8000/query"
        
    payload = {
        "text": text
    }     
    try:
        response = requests.post(url, json=payload)
              
        if response.status_code == 200:
            data = response.json()
          
            try:
                actual_response = data['candidates'][0]['content']['parts'][0]['text']
                
                
                print_streaming(actual_response)
               
            except (KeyError, IndexError):
                print("Unexpected response format:", json.dumps(data, indent=2))
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the server. Make sure the server is running ")
    except Exception as e:
        print(f"Error: {str(e)}")

def format_history_entry(entry):    
    print(f"Time: {entry['timestamp']}")
    print(f"Query: ", end='', flush=True)
    print_streaming(entry['query'])
    print(f"Response: ", end='', flush=True)
    print_streaming(entry['response'])
    print("-" * 50)

def view_history():
    url = "http://localhost:8000/history"    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            history = response.json()
            print("\nChat History:")
            print("-" * 50)
            for entry in history:
                format_history_entry(entry)
        else:
            print(f"Error fetching history: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to the server. Make sure the server ")
    except Exception as e:
        print(f"Error: {str(e)}")

def print_welcome():
    welcome_message = "Welcome to ChatTRC !"
    instructions = "Type 'quit' to exit or 'history' to view chat history"
       
    print_streaming(welcome_message)
    print_streaming(instructions)

def print_streaming(text):
   
    tokens = re.findall(r'\w+|\s+|[^\w\s]', text)
    
    for token in tokens:
        print(token, end='', flush=True)
        time.sleep(0.1)
    print() 

def main():
    print_welcome()
    
    while True:
        try:
            user_input = input("\nYour Query: ").strip()
            
            if user_input.lower() == 'quit':
                
                break
            elif user_input.lower() == 'history':
                view_history()
            elif user_input:
                send_query(user_input)
            else:
                print_streaming("Plz enter a valid query")
                
        except KeyboardInterrupt:
           
            break
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()