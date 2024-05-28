import streamlit as st
import base64
from llm_query import get_image_informations, farma_chatbot
import streamlit as st
import streamlit.components.v1 as components


if "language" not in st.session_state:
    st.session_state.language = "English"

if "sidebar_" not in st.session_state:
    st.session_state.sidebar_ = False

if "chatbot" not in st.session_state:
    st.session_state.chatbot = False

if "initial_upload" not in st.session_state:
    st.session_state.initial_upload = True

if "results_print" not in st.session_state:
    st.session_state.results_print = False

if "farma_chatbot" not in st.session_state:
    st.session_state.farma_chatbot = farma_chatbot()

if "results" not in st.session_state:
    st.session_state.results = {}


def sidebar_():
    with st.sidebar:
        st.title("Ask me your Agriculture doubts!!!!")


def main():
    content_placeholder = st.empty()
    chatbot_placeholder = st.empty()
    

    if st.session_state.initial_upload:
        with content_placeholder.container():
            st.title("FarmaCare")

            option = st.selectbox(
                "Select an option",
                ("Image Upload", "Current Location")
            )
            if option == "Image Upload":
                file = st.file_uploader(f"Upload the image of the soil")
                if file is not None:
                    try:
                        bytes_data = file.read()
                        base64_data = base64.b64encode(bytes_data).decode('utf-8')
                        results = get_image_informations(base64_data)
                        if results:
                            st.session_state.results_print = True
                            st.session_state.initial_upload = False
                            st.session_state.results = results
                            
                    except:
                        st.write("Please upload a valid image")    
            else:
                location = st.empty()
                if st.button('Get Location'):
    # JavaScript to get the geolocation and send it back to Streamlit
                    geolocation_script = """
                    <script>
                    function getLocation() {
                        navigator.geolocation.getCurrentPosition(
                            (position) => {
                                const latitude = position.coords.latitude;
                                const longitude = position.coords.longitude;
                                const accuracy = position.coords.accuracy;
                
                                // Send data to Streamlit via URL parameters
                                const params = new URLSearchParams(window.location.search);
                                params.set("latitude", latitude);
                                params.set("longitude", longitude);
                                params.set("accuracy", accuracy);
                
                                window.location.search = params.toString();
                            },
                            (error) => {
                                console.error(error);
                                alert('Unable to retrieve your location');
                            }
                        );
                    }
                    getLocation();
                    </script>
                    """
                    # Embedding the JavaScript code in the Streamlit app
                    components.html(geolocation_script)
                
                # Extract the geolocation data from URL parameters
                query_params = st.query_params()
                print("#################################")
                print(query_params)
                latitude = query_params.get("latitude", [None])[0]
                longitude = query_params.get("longitude", [None])[0]
                accuracy = query_params.get("accuracy", [None])[0]
                
                if latitude and longitude:
                    location.write(f"Latitude: {latitude}, Longitude: {longitude}, Accuracy: {accuracy} meters")
                else:
                    location.write("Waiting for location data...")

    if st.session_state.results_print:
        content_placeholder.empty()
        with content_placeholder.container():
            st.title("FarmaCare")
            st.header("_Soil Type_", divider="rainbow")
            st.write(st.session_state.results["soil_type"])
            st.header("_Crops Suitable_", divider="rainbow")
            st.write(st.session_state.results["crops_suitable"])
            st.header("_Description_", divider="rainbow")
            st.write(st.session_state.results["short_description"])
            if st.button("Let's Chat !!!!"):
                st.session_state.chatbot = True
                st.session_state.results_print = False 
                st.session_state.sidebar_ = True
    
    if st.session_state.sidebar_:
        with st.sidebar:
            option = st.selectbox(
            "Select Language",
            ("English", "Hindi", "Kannada", "Tamil", "Malayalam", "Telugu"))
            language_dict = {
                "English": "en",
                "Hindi": "hi",
                "Kannada" : "kn",
                "Tamil" : "ta",
                "Malayalam" : "ml",
                "Telugu" : "te"
            }
            st.session_state.language = option

    if st.session_state.chatbot:
        content_placeholder.empty()
        st.title("FarmaCare Bot!!")
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask me something"):
            st.chat_message("user").markdown(prompt)
            st.session_state.farma_chatbot.update_user_message(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            response = st.session_state.farma_chatbot.chatbot_runner(st.session_state.results, prompt)
            st.session_state.farma_chatbot.update_ai_message(response)
            if st.session_state.language == "English":
                with st.chat_message("assistant"):
                    st.markdown(response)
            else:
                response_translated = st.session_state.farma_chatbot.translator_for_bot(response, st.session_state.language)
                with st.chat_message("assistant"):
                    st.markdown(response_translated)
            st.session_state.messages.append({"role": "assistant", "content": response})     

                



if __name__ == "__main__":
    main()
