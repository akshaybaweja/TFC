from __future__ import print_function
import time
import datetime
import boto3
# --------------- Helpers that build all of the responses ----------------------
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_speechlet_response_without_card(output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_dialog_delegate(output, should_end_session, intent):
    return {
        'shouldEndSession': should_end_session,
        'directives': [
            {
                'type': 'Dialog.Delegate',
                'updatedIntent': {
                    'name': intent['name'],
                    'confirmationStatus': intent['confirmationStatus'],
                    'slots': intent['slots']
                }
            }
        ]
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    card_title = "Welcome"
    session_attributes = {}
    should_end_session = False
    speech_output = "Welcome to The Founder's Cafe. How may I help you"
    reprompt_text=speech_output
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def make_complain_suggestion(intent, session, deviceId):
    card_title = "Complaint/Suggestion"
    session_attributes = {}
    should_end_session = True
    speech_output = "Thanks, I will let the community manager know about it."
    reprompt_text = speech_output
    if not "value" in intent['slots']['Description']:
        return get_complain_suggestion_description(intent,session)
    else:
        reportType = intent['slots']['type']['value']
        message = intent['slots']['Description']['value']
        print("TYPE: "+reportType+"    MESSAGE: "+message)

        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%d-%m-%Y %H:%M:%S')
        client = boto3.client('dynamodb')
        client.put_item(
            TableName='tfc-suggestion-complaint',
            Item={
                'timestamp':{'S':timestamp},
                'deviceId':{'S':deviceId},
                'message':{'S':message},
                'type':{'S':reportType}
                })

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_complain_suggestion_description(intent, session):
    session_attributes={}
    should_end_session = False
    speech_output = "Thanks, I will let the community manager know about it."
    return build_response(session_attributes, build_dialog_delegate(
        speech_output, should_end_session,intent))

def handle_session_end_request():
    card_title = "Thank you"
    speech_output = "Thank you"
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def get_help():
    card_title = "Help"
    session_attributes = {}
    speech_output = "Help"
    should_end_session = False
    reprompt_text=speech_output
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session, deviceId):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "ComplaintSuggestion":
        return make_complain_suggestion(intent, session, deviceId)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help(intent,session)
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
    print("event.session.application.applicationId=" + 
        event['session']['application']['applicationId'])
    
    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'], 
            event["context"]["System"]["device"]["deviceId"])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])