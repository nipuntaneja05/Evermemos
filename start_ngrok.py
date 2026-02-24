from pyngrok import ngrok
import time

def start_ngrok():
    print("Starting ngrok tunnel to port 8501...")
    # Open a HTTP tunnel on the default port 8501 (Streamlit)
    public_url = ngrok.connect(8501)
    
    print("=" * 60)
    print("NGROK TUNNEL CREATED SUCCESSFULLY!")
    print(f"Public URL: {public_url}")
    print("=" * 60)
    with open("ngrok_url.txt", "w") as f:
        f.write(str(public_url))
        
    print("\nAnyone given this link can view the Streamlit interface.")
    print("Keeping tunnel open...")
    
    while True:
        time.sleep(10)

if __name__ == "__main__":
    start_ngrok()
