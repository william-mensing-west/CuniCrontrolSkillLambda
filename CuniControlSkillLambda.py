"""
This is the Cuni Control skill lambda handler.  This handler is part of the CUNI AI project
that interacts with AWS IoT devices through the device shadow.  The project allows the user
to locate objects using Jetson Nano AI and get the temperature an humidity from a Mega 2560.
The Nano and Mega are AWS IoT devices that sync with their device shadows.  The main intents 
used are the "FindObjectIntent", "GetTemperature", and "GetHumidity". "FindObjectIntent" is 
used to locate objects by setting the desired "find" property on the Cam0 device.   
"GetTemperature" is used to retrun the temperature in fahrenheit. "GetHumidity" is used to retrun
the percent humidity from the Mega interface device shadow.

Shadow JSON schema:
Name: Cam0
{
 	"state": {
 		"desired":{
            "find": <modelClassLabel>,
            "timeoutSec": <1:3600>,
            "objectdetection": "<INIT|SEARCHING|FOUND|NOT_FOUND>",
 			"panangle": <0:180>,
 			"tiltangle": <0:180>
 		}
 	}
}

The MegaIf1 device shadow has the following reported properties:

Name: MegaIf1
{
    "reported":{ 
        "TemperatureF":<n>, 
        "TemperatureFMax":<n>, 
        "TemperatureFMin":<n>,
        "Humidity":"<n>",
        "HumidityMin":"<n>",
        "HumidityMax":"<n>",
        "ReportIntervalMinutes":<min>
    }
}

MIT License
Copyright (c) 2020 William West
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import print_function
import boto3
import json

client = boto3.client('iot-data', region_name='us-east-1',
       aws_access_key_id='MyId',
       aws_secret_access_key='MySecretKey'
       )


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    """
        **Description**

        Helper function to build all the responses

        **Parameters**

        *title* - The title of the card displayed in the Alexa app.

        *output* - The content of the card and speech output.

        *reprompt_text* - The utterance if the intent is not understood.

        *should_end_session* - A value indicating wether or not the session should end

        
        **Returns**
        JSON formatted response parameters
        
    """

    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    """
        **Description**

        Helper function to build responses that have session attributes

        **Parameters**

        *session_attributes* - The title of the card displayed in the Alexa app.

        *speechlet_response* - The content of the card and speech output.
        
        **Returns**
        JSON formatted response response and session attributes
        
    """
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------  Helpers to update the shadow devices -----------------------------
def set_thing_state(thingName, desiredProperty, state):
    """
        **Description**

        Sets the IoT device shadow desired property value by posting to the device topic

        **Parameters**

        *thingName* - The name of the device to update.

        *desiredProperty* - The property name of device to update.

        *state* - The value of the property to set.

        
        **Returns**
        (dict) -- The output from the UpdateThingShadow operation.

            payload (StreamingBody) -- The state information, in JSON format. 
        
    """

    # build a JSON fromatted payload
    payload = json.dumps({'state': { 'desired': { desiredProperty : state } }})

    print("IOT update, thingName:"+ thingName +", payload:" + payload)
    #payload = {'state': { 'desired': { 'property': value } }}          

    response = client.update_thing_shadow(
        thingName = thingName, 
        payload =  payload
        )

    print("IOT response: " + str(response))  

    return response


def get_thing_state(thingName, thingProperty):
    """
        **Description**

        Gets the IoT device shadow document and read the property value

        **Parameters**

        *thingName* - The name of the device shadow to get.

        *thingProperty* - The property name of device shadow to read.
        
        **Returns**
        The value of the response property from the shadow device
        
    """
    response = client.get_thing_shadow(thingName=thingName)

    streamingBody = response["payload"]
    jsonState = json.loads(streamingBody.read())
    print(jsonState)

    thingPropVal = jsonState["state"]["reported"][thingProperty]
    print(thingPropVal)

    return thingPropVal


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """
        **Description**

        Formulate the welcome message for the CuniControl skill
        
        **Returns**
        JSON formatted output speech, card, reprompt text, and should session end information.

    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Cuni Control. " \
                    "You can find any COCO data set object by saying, Find a book, TV, Mouse, bottle other objects.  " \
                    "You can also ask, What is the temperature or humidity."
    
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell what to find, " \
                    "a fork, spoon, knife, chair, or potted plant."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    """
        **Description**

        Formulate the message when ending CuniControl skill
        
        **Returns**
        JSON formatted output speech, card, reprompt text, and should session end information.
        
    """
    card_title = "Session Ended"
    speech_output = "Thank you for trying Cuni Control. " \
                    "Have a nice day! "
    
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def set_find_object(intent, session):
    """
        **Description**

        Sets the desired object to find in the AWS IoT cam0 shadow device

        **Parameters**

        *intent* - The intent from the main handler.

        *session* - The session variables from the main handler.
        
        **Returns**
        JSON formatted response with output speech, card, reprompt text, and should session end information.
        
    """

    session_attributes = {}
    card_title = intent['name']
    should_end_session = False

    # gets the name of the object to find from the CocoLabels 
    if 'CocoLabel' in intent['slots']:
        find_object = intent['slots']['CocoLabel']['value']

        # update the cam0 shadow device
        set_thing_state("cam0", "find", find_object)

        speech_output = "I am now looking for a " +  find_object 
        reprompt_text = ""
        should_end_session = True
    else:
        speech_output = "I'm not sure what you want me to find. " \
                        "Please try again."
        reprompt_text = "I'm not sure what you want me to find. " \
                        "You can ask me to look for objects by saying, " \
                        "Find a fork, knife, or spoon."

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
        


def get_temp(intent, session):
    """
        **Description**

        Reads the response temperature property value from the Mega interface shadow device 

        **Parameters**

        *intent* - The intent from the main handler.

        *session* - The session variables from the main handler.
        
        **Returns**
        JSON formatted response with output speech, card, reprompt text, and should session end information.
        
    """
    session_attributes = {}
    reprompt_text = None

    temp = get_thing_state("MegaIf1", "TemperatureF")
    speech_output = "The temperature is " + temp + " degrees. " \
                        ". Goodbye."
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def get_humidity(intent, session):
    """
        **Description**

        Reads the response humidity property value from the Mega interface shadow device 

        **Parameters**

        *intent* - The intent from the main handler.

        *session* - The session variables from the main handler.
        
        **Returns**
        JSON formatted response with output speech, card, reprompt text, and should session end information.
        
    """

    session_attributes = {}
    reprompt_text = None

    humidity = get_thing_state("MegaIf1", "Humidity%")
    speech_output = "The humidity is " + humidity + " percent. " \
                        ". Goodbye."
    should_end_session = True
    
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

def set_pan_angle(intent, session):
    """
        **Description**

        Sets the desired pan angle on the cam0 camera assembly shadow device 

        **Parameters**

        *intent* - The intent from the main handler.

        *session* - The session variables from the main handler.
        
        **Returns**
        JSON formatted response with output speech, card, reprompt text, and should session end information.
        
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'angle' in intent['slots']:
        pan_angle = intent['slots']['angle']['value']

        speech_output = "I am setting the pan angle to " + pan_angle
        
        # update the shadow device
        set_thing_state("cam0", "panAngle", pan_angle)

        reprompt_text = None
    else:
        speech_output = "I'm not sure what your pan angle is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your pan angle is. " \
                        "You can tell me your pan color by saying, " \
                        "set pan angle to 90."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """
        **Description**

        This event is called when the session starts
        
        **Returns**
        None
        
    """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """
        **Description**

        This event is called when the user launches the skill without specifying what they
    want
        
        **Returns**
        None
        
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "FindObjectIntent":
        return set_find_object(intent, session)
    elif intent_name == "GetTemperature":
        return get_temp(intent, session)
    elif intent_name == "GetHumidity":
        return get_humidity(intent, session)
    elif intent_name == "SetPanIntent":
        return set_pan_angle(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
